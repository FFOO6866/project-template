"""
Multi-Tenant Configuration for DataFlow Sales Assistant
======================================================

This module demonstrates comprehensive multi-tenancy configuration including:
- Tenant isolation strategies
- Row-level security implementation
- Cross-tenant data access patterns
- Tenant-specific customizations
- Performance optimization for multi-tenant scenarios
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataflow import DataFlow, DataFlowConfig, Environment
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# ==============================================================================
# MULTI-TENANT DATAFLOW CONFIGURATION
# ==============================================================================

class MultiTenantDataFlowConfig:
    """Configuration class for multi-tenant DataFlow setup"""
    
    @staticmethod
    def create_production_config() -> DataFlow:
        """Create production-ready multi-tenant DataFlow configuration"""
        
        config = DataFlowConfig(
            environment=Environment.PRODUCTION,
            
            # Multi-tenancy settings
            multi_tenant=True,
            tenant_isolation_mode="strict",  # strict, standard, loose
            
            # Performance settings
            connection_pool_size=50,
            connection_pool_max_overflow=100,
            connection_pool_recycle=3600,
            
            # Security settings
            enable_row_level_security=True,
            audit_all_operations=True,
            encrypt_sensitive_fields=True,
            
            # Monitoring settings
            monitoring=True,
            performance_tracking=True,
            slow_query_threshold=1000,  # 1 second
            
            # Cache settings
            enable_redis_cache=True,
            cache_default_ttl=300,  # 5 minutes
            cache_max_size_mb=1024,  # 1GB
        )
        
        # PostgreSQL connection with multi-tenant optimizations
        db = DataFlow(
            config=config,
            database_url="postgresql://sales_app:secure_password@localhost:5432/sales_assistant_prod",
            
            # Advanced PostgreSQL settings for multi-tenancy
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30,
            
            # Enable connection pooling per tenant
            tenant_connection_pooling=True,
            max_connections_per_tenant=10,
            
            # Row-level security
            enable_rls=True,
            rls_policy_mode="automatic"
        )
        
        return db
    
    @staticmethod
    def create_development_config() -> DataFlow:
        """Create development DataFlow configuration with debugging"""
        
        config = DataFlowConfig(
            environment=Environment.DEVELOPMENT,
            multi_tenant=True,
            monitoring=True,
            debug_mode=True
        )
        
        db = DataFlow(
            config=config,
            database_url="postgresql://dev_user:dev_pass@localhost:5432/sales_assistant_dev",
            echo=True,  # Enable SQL logging for development
            auto_migrate=True  # Enable auto-migration in development
        )
        
        return db

# ==============================================================================
# TENANT MANAGEMENT UTILITIES
# ==============================================================================

class TenantManager:
    """Utility class for managing tenant operations"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def create_tenant(self, tenant_data: Dict[str, Any]) -> str:
        """Create a new tenant with proper isolation setup"""
        
        workflow = WorkflowBuilder()
        
        # 1. Create company/tenant record
        workflow.add_node("CompanyCreateNode", "create_tenant", {
            "name": tenant_data["name"],
            "domain": tenant_data["domain"],
            "industry": tenant_data.get("industry", "General"),
            "address": tenant_data.get("address", ""),
            "phone": tenant_data.get("phone", ""),
            "email": tenant_data.get("email", ""),
            "settings": {
                "timezone": tenant_data.get("timezone", "UTC"),
                "currency": tenant_data.get("currency", "USD"),
                "date_format": tenant_data.get("date_format", "YYYY-MM-DD"),
                "number_format": tenant_data.get("number_format", "US")
            },
            "erp_config": tenant_data.get("erp_config", {}),
            "active": True
        })
        
        # 2. Create default admin user for tenant
        workflow.add_node("UserCreateNode", "create_admin", {
            "first_name": tenant_data.get("admin_first_name", "Admin"),
            "last_name": tenant_data.get("admin_last_name", "User"),
            "email": tenant_data.get("admin_email"),
            "role": "admin",
            "department": "Management",
            "is_active": True,
            "preferences": {
                "dashboard_layout": "default",
                "notification_settings": {
                    "email_notifications": True,
                    "in_app_notifications": True
                }
            }
        })
        workflow.add_connection("create_tenant", "id", "create_admin", "company_id")
        
        # 3. Initialize tenant-specific configurations
        default_configs = [
            {
                "config_key": "quote_number_format",
                "config_value": "Q-{YYYY}{MM}{DD}-{###}",
                "config_type": "string",
                "category": "system",
                "description": "Format for auto-generated quote numbers"
            },
            {
                "config_key": "default_quote_validity_days",
                "config_value": "30",
                "config_type": "integer",
                "category": "business",
                "description": "Default validity period for quotes in days"
            },
            {
                "config_key": "auto_approve_threshold",
                "config_value": "10000.00",
                "config_type": "float",
                "category": "business",
                "description": "Quote amount threshold for automatic approval"
            },
            {
                "config_key": "ai_confidence_threshold",
                "config_value": "0.85",
                "config_type": "float",
                "category": "ai",
                "description": "Minimum confidence score for AI document processing"
            }
        ]
        
        for i, config in enumerate(default_configs):
            workflow.add_node("SystemConfigurationCreateNode", f"create_config_{i}", config)
            workflow.add_connection("create_tenant", "id", f"create_config_{i}", "tenant_id")
        
        # Execute tenant creation workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        tenant_id = results.get("create_tenant", {}).get("id")
        return str(tenant_id) if tenant_id else None
    
    def setup_tenant_isolation(self, tenant_id: str) -> bool:
        """Setup row-level security policies for tenant isolation"""
        
        workflow = WorkflowBuilder()
        
        # Create RLS policies for each tenant-aware table
        tenant_tables = [
            "users", "customers", "quotes", "quote_line_items",
            "documents", "erp_products", "activity_logs",
            "business_metrics", "system_configurations"
        ]
        
        for table in tenant_tables:
            # Enable RLS on table
            workflow.add_node("ExecuteSQLNode", f"enable_rls_{table}", {
                "sql": f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;",
                "execute_as": "admin"
            })
            
            # Create tenant isolation policy
            workflow.add_node("ExecuteSQLNode", f"create_policy_{table}", {
                "sql": f"""
                CREATE POLICY tenant_isolation_{table} ON {table}
                USING (tenant_id = current_setting('app.current_tenant_id')::integer);
                """,
                "execute_as": "admin"
            })
        
        # Execute RLS setup
        results, run_id = self.runtime.execute(workflow.build())
        return all(result.get("status") == "success" for result in results.values())
    
    def switch_tenant_context(self, tenant_id: str) -> WorkflowBuilder:
        """Create workflow with tenant context set"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # Set PostgreSQL session variable for RLS
        workflow.add_node("ExecuteSQLNode", "set_tenant_context", {
            "sql": f"SET app.current_tenant_id = '{tenant_id}';",
            "execute_as": "application"
        })
        
        return workflow
    
    def get_tenant_metrics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive metrics for a specific tenant"""
        
        workflow = self.switch_tenant_context(tenant_id)
        
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Customer metrics
        workflow.add_node("CustomerListNode", "customer_metrics", {
            "aggregate": [
                {
                    "$group": {
                        "_id": None,
                        "total_customers": {"$sum": 1},
                        "active_customers": {
                            "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                        },
                        "total_lifetime_value": {"$sum": "$lifetime_value"}
                    }
                }
            ]
        })
        
        # 2. Quote metrics
        workflow.add_node("QuoteListNode", "quote_metrics", {
            "filter": {
                "created_date": {"$gte": start_date}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_value": {"$sum": "$total_amount"}
                    }
                }
            ]
        })
        
        # 3. Document processing metrics
        workflow.add_node("DocumentListNode", "document_metrics", {
            "filter": {
                "upload_date": {"$gte": start_date}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$ai_status",
                        "count": {"$sum": 1}
                    }
                }
            ]
        })
        
        # 4. User activity metrics
        workflow.add_node("ActivityLogListNode", "activity_metrics", {
            "filter": {
                "timestamp": {"$gte": start_date}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$user_id",
                        "activity_count": {"$sum": 1}
                    }
                }
            ]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "customers": results.get("customer_metrics", {}).get("result", []),
            "quotes": results.get("quote_metrics", {}).get("result", []),
            "documents": results.get("document_metrics", {}).get("result", []),
            "activities": results.get("activity_metrics", {}).get("result", [])
        }

# ==============================================================================
# CROSS-TENANT DATA ACCESS PATTERNS
# ==============================================================================

class CrossTenantDataAccess:
    """Utilities for controlled cross-tenant data access"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def get_platform_metrics(self, requesting_tenant_id: str) -> Dict[str, Any]:
        """Get platform-wide metrics (requires super-admin privileges)"""
        
        # Verify requesting tenant has platform admin privileges
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = requesting_tenant_id
        
        workflow.add_node("UserListNode", "verify_admin", {
            "filter": {
                "company_id": int(requesting_tenant_id),
                "role": "platform_admin",
                "is_active": True
            },
            "limit": 1
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        if not results.get("verify_admin", {}).get("result"):
            raise PermissionError("Access denied: Platform admin privileges required")
        
        # Get platform-wide metrics with elevated privileges
        workflow = WorkflowBuilder()
        workflow.metadata["bypass_tenant_isolation"] = True
        
        # Total customers across all tenants
        workflow.add_node("CustomerListNode", "all_customers", {
            "aggregate": [
                {
                    "$group": {
                        "_id": "$tenant_id", 
                        "customer_count": {"$sum": 1}
                    }
                }
            ]
        })
        
        # Total quotes across all tenants
        workflow.add_node("QuoteListNode", "all_quotes", {
            "aggregate": [
                {
                    "$group": {
                        "_id": "$tenant_id",
                        "quote_count": {"$sum": 1},
                        "total_value": {"$sum": "$total_amount"}
                    }
                }
            ]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "platform_customers": results.get("all_customers", {}).get("result", []),
            "platform_quotes": results.get("all_quotes", {}).get("result", []),
            "generated_at": datetime.now().isoformat()
        }
    
    def share_quote_template_across_tenants(
        self, 
        template_id: int, 
        source_tenant_id: str, 
        target_tenant_ids: List[str]
    ) -> bool:
        """Share a quote template across multiple tenants"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = source_tenant_id
        
        # 1. Get source template
        workflow.add_node("QuoteTemplateReadNode", "get_template", {
            "conditions": {"id": template_id}
        })
        
        # 2. For each target tenant, create a copy
        for i, target_tenant_id in enumerate(target_tenant_ids):
            workflow.add_node("QuoteTemplateCreateNode", f"share_to_{i}", {
                "name": f"Shared: {template_id}",  # Will be updated with actual name
                "category": "shared",
                "template_data": {},  # Will be populated from source
                "created_by": 1,  # System user
                "is_public": True
            })
            workflow.metadata[f"target_tenant_{i}"] = target_tenant_id
        
        results, run_id = self.runtime.execute(workflow.build())
        return all(result.get("status") == "success" for result in results.values())

# ==============================================================================
# TENANT-SPECIFIC CUSTOMIZATIONS
# ==============================================================================

class TenantCustomizations:
    """Handle tenant-specific customizations and configurations"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def apply_tenant_customizations(self, tenant_id: str, customizations: Dict[str, Any]) -> bool:
        """Apply tenant-specific customizations"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Update company settings
        if "company_settings" in customizations:
            workflow.add_node("CompanyUpdateNode", "update_settings", {
                "conditions": {"id": int(tenant_id)},
                "updates": {"settings": customizations["company_settings"]}
            })
        
        # 2. Update system configurations
        if "system_configs" in customizations:
            for config_key, config_value in customizations["system_configs"].items():
                workflow.add_node("SystemConfigurationBulkUpsertNode", f"config_{config_key}", {
                    "data": [{
                        "config_key": config_key,
                        "config_value": str(config_value),
                        "config_type": type(config_value).__name__.lower(),
                        "category": "tenant_custom",
                        "updated_at": datetime.now()
                    }],
                    "match_fields": ["config_key", "tenant_id"]
                })
        
        # 3. Create custom quote templates if provided
        if "quote_templates" in customizations:
            for i, template in enumerate(customizations["quote_templates"]):
                workflow.add_node("QuoteTemplateCreateNode", f"template_{i}", {
                    "name": template["name"],
                    "description": template.get("description"),
                    "category": template.get("category", "custom"),
                    "industry": template.get("industry"),
                    "template_data": template["data"],
                    "created_by": 1,  # System user
                    "is_public": template.get("is_public", False)
                })
        
        results, run_id = self.runtime.execute(workflow.build())
        return all(result.get("status") == "success" for result in results.values())
    
    def get_tenant_customizations(self, tenant_id: str) -> Dict[str, Any]:
        """Retrieve all customizations for a tenant"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Get company settings
        workflow.add_node("CompanyReadNode", "get_company", {
            "conditions": {"id": int(tenant_id)}
        })
        
        # 2. Get system configurations
        workflow.add_node("SystemConfigurationListNode", "get_configs", {
            "filter": {"category": "tenant_custom"}
        })
        
        # 3. Get custom quote templates
        workflow.add_node("QuoteTemplateListNode", "get_templates", {
            "filter": {"category": "custom"}
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "company_settings": results.get("get_company", {}).get("result", {}).get("settings", {}),
            "system_configs": {
                config["config_key"]: config["config_value"] 
                for config in results.get("get_configs", {}).get("result", [])
            },
            "quote_templates": results.get("get_templates", {}).get("result", [])
        }

# ==============================================================================
# PERFORMANCE OPTIMIZATION FOR MULTI-TENANT SCENARIOS
# ==============================================================================

class MultiTenantPerformanceOptimizer:
    """Performance optimization utilities for multi-tenant scenarios"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def optimize_tenant_queries(self, tenant_id: str) -> Dict[str, Any]:
        """Analyze and optimize queries for a specific tenant"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Analyze query patterns
        workflow.add_node("AnalyzeQueriesNode", "analyze_patterns", {
            "tenant_id": tenant_id,
            "analysis_period_days": 7,
            "include_slow_queries": True
        })
        
        # 2. Generate index recommendations
        workflow.add_node("GenerateIndexRecommendationsNode", "index_recommendations", {
            "tenant_id": tenant_id,
            "min_query_frequency": 10,
            "min_performance_impact": 0.1
        })
        
        # 3. Analyze data distribution
        workflow.add_node("AnalyzeDataDistributionNode", "data_distribution", {
            "tenant_id": tenant_id,
            "tables": ["customers", "quotes", "documents"]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "query_patterns": results.get("analyze_patterns", {}).get("result", {}),
            "index_recommendations": results.get("index_recommendations", {}).get("result", []),
            "data_distribution": results.get("data_distribution", {}).get("result", {}),
            "optimization_timestamp": datetime.now().isoformat()
        }
    
    def implement_tenant_specific_indexes(self, tenant_id: str, indexes: List[Dict]) -> bool:
        """Implement tenant-specific database indexes"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        for i, index in enumerate(indexes):
            # Create partial indexes filtered by tenant_id for better performance
            index_sql = f"""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}_{tenant_id}
            ON {index['table']} ({', '.join(index['columns'])})
            WHERE tenant_id = {tenant_id};
            """
            
            workflow.add_node("ExecuteSQLNode", f"create_index_{i}", {
                "sql": index_sql,
                "execute_as": "admin",
                "timeout": 300  # 5 minutes for index creation
            })
        
        results, run_id = self.runtime.execute(workflow.build())
        return all(result.get("status") == "success" for result in results.values())

# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

def demo_multi_tenant_setup():
    """Demonstrate multi-tenant DataFlow setup and usage"""
    
    print("=== Multi-Tenant DataFlow Demo ===")
    
    # 1. Create production DataFlow instance
    db = MultiTenantDataFlowConfig.create_production_config()
    tenant_manager = TenantManager(db)
    
    # 2. Create first tenant
    print("\n--- Creating Tenant 1: Manufacturing Company ---")
    tenant1_id = tenant_manager.create_tenant({
        "name": "Acme Manufacturing Corp",
        "domain": "acme-mfg.com",
        "industry": "Manufacturing",
        "admin_email": "admin@acme-mfg.com",
        "admin_first_name": "John",
        "admin_last_name": "Smith",
        "timezone": "America/New_York",
        "currency": "USD",
        "erp_config": {
            "system": "SAP",
            "endpoint": "https://sap.acme-mfg.com",
            "integration_enabled": True
        }
    })
    print(f"Tenant 1 created with ID: {tenant1_id}")
    
    # 3. Create second tenant
    print("\n--- Creating Tenant 2: Technology Services ---")
    tenant2_id = tenant_manager.create_tenant({
        "name": "TechServ Solutions Ltd",
        "domain": "techserv.co.uk",
        "industry": "Technology Services",
        "admin_email": "admin@techserv.co.uk",
        "admin_first_name": "Sarah",
        "admin_last_name": "Johnson",
        "timezone": "Europe/London",
        "currency": "GBP",
        "erp_config": {
            "system": "NetSuite",
            "endpoint": "https://netsuite.techserv.co.uk",
            "integration_enabled": True
        }
    })
    print(f"Tenant 2 created with ID: {tenant2_id}")
    
    # 4. Setup tenant isolation
    print("\n--- Setting up tenant isolation ---")
    tenant_manager.setup_tenant_isolation(tenant1_id)
    tenant_manager.setup_tenant_isolation(tenant2_id)
    print("Tenant isolation configured")
    
    # 5. Demonstrate tenant-specific operations
    print("\n--- Tenant-specific operations ---")
    
    # Create customer for tenant 1
    workflow1 = tenant_manager.switch_tenant_context(tenant1_id)
    workflow1.add_node("CustomerCreateNode", "create_customer_t1", {
        "name": "Industrial Solutions Inc",
        "type": "business",
        "industry": "Industrial",
        "primary_contact": "Mike Wilson",
        "email": "mike@industrial-solutions.com",
        "phone": "+1-555-1234",
        "billing_address": {
            "street": "456 Industrial Blvd",
            "city": "Detroit",
            "state": "MI",
            "zip": "48201",
            "country": "USA"
        }
    })
    
    runtime = LocalRuntime()
    results1, _ = runtime.execute(workflow1.build())
    print(f"Customer created for Tenant 1: {results1.get('create_customer_t1', {}).get('id')}")
    
    # Create customer for tenant 2
    workflow2 = tenant_manager.switch_tenant_context(tenant2_id)
    workflow2.add_node("CustomerCreateNode", "create_customer_t2", {
        "name": "Digital Innovations Ltd",
        "type": "business",
        "industry": "Technology",
        "primary_contact": "Emma Thompson",
        "email": "emma@digital-innovations.co.uk",
        "phone": "+44-20-1234-5678",
        "billing_address": {
            "street": "789 Tech Park Way",
            "city": "London",
            "state": "",
            "zip": "SW1A 1AA",
            "country": "UK"
        }
    })
    
    results2, _ = runtime.execute(workflow2.build())
    print(f"Customer created for Tenant 2: {results2.get('create_customer_t2', {}).get('id')}")
    
    # 6. Get tenant metrics
    print("\n--- Tenant Metrics ---")
    metrics1 = tenant_manager.get_tenant_metrics(tenant1_id)
    metrics2 = tenant_manager.get_tenant_metrics(tenant2_id)
    
    print(f"Tenant 1 metrics: {len(metrics1.get('customers', []))} customers")
    print(f"Tenant 2 metrics: {len(metrics2.get('customers', []))} customers")
    
    # 7. Demonstrate customizations
    print("\n--- Applying Tenant Customizations ---")
    customizer = TenantCustomizations(db)
    
    # Customize tenant 1 for manufacturing
    customizer.apply_tenant_customizations(tenant1_id, {
        "company_settings": {
            "default_lead_time_days": 14,
            "manufacturing_focus": True,
            "quality_certification": "ISO 9001"
        },
        "system_configs": {
            "quote_approval_threshold": 25000.00,
            "default_warranty_months": 24
        }
    })
    
    # Customize tenant 2 for technology services
    customizer.apply_tenant_customizations(tenant2_id, {
        "company_settings": {
            "service_focus": True,
            "consultation_rates": True,
            "project_based_pricing": True
        },
        "system_configs": {
            "quote_approval_threshold": 50000.00,
            "default_service_period_months": 12
        }
    })
    
    print("Tenant customizations applied successfully")
    
    print("\n=== Multi-Tenant Setup Complete ===")

if __name__ == "__main__":
    demo_multi_tenant_setup()