"""
DataFlow Implementation Patterns for AI-Powered Sales Assistant
==============================================================

This module demonstrates comprehensive DataFlow usage patterns including:
- Customer management workflows
- Quote generation with line items
- Document processing pipelines
- ERP synchronization patterns
- Multi-tenant operations
- Performance optimization strategies
- Transaction handling patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataflow_models import (
    db, Company, User, Customer, Quote, QuoteLineItem, 
    Document, ERPProduct, ActivityLog, BusinessMetrics
)
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# ==============================================================================
# CUSTOMER MANAGEMENT PATTERNS
# ==============================================================================

class CustomerManagementService:
    """Service class demonstrating customer management patterns"""
    
    @staticmethod
    def create_customer_workflow(customer_data: Dict[str, Any], tenant_id: str) -> WorkflowBuilder:
        """Create a comprehensive customer onboarding workflow"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Create customer record
        workflow.add_node("CustomerCreateNode", "create_customer", customer_data)
        
        # 2. Create default billing address if not provided
        if "shipping_address" not in customer_data and "billing_address" in customer_data:
            workflow.add_node("CustomerUpdateNode", "set_shipping_address", {
                "updates": {"shipping_address": customer_data["billing_address"]}
            })
            workflow.add_connection("create_customer", "id", "set_shipping_address", "customer_id")
        
        # 3. Log customer creation activity
        workflow.add_node("ActivityLogCreateNode", "log_creation", {
            "entity_type": "customer",
            "action": "create",
            "user_name": "System",
            "user_role": "system",
            "ip_address": "127.0.0.1",
            "user_agent": "DataFlow System",
            "timestamp": datetime.now(),
            "change_summary": f"New customer created: {customer_data.get('name', 'Unknown')}"
        })
        workflow.add_connection("create_customer", "id", "log_creation", "entity_id")
        
        # 4. Initialize customer metrics
        workflow.add_node("BusinessMetricsCreateNode", "init_metrics", {
            "metric_name": "customer_lifetime_value",
            "metric_category": "customer",
            "metric_value": 0.0,
            "metric_unit": "currency",
            "period_type": "lifetime",
            "period_start": datetime.now(),
            "period_end": datetime.now() + timedelta(days=365*5)  # 5 year projection
        })
        workflow.add_connection("create_customer", "id", "init_metrics", "customer_id")
        
        return workflow
    
    @staticmethod
    def search_customers_workflow(search_criteria: Dict[str, Any], tenant_id: str) -> WorkflowBuilder:
        """Advanced customer search with MongoDB-style queries"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # Build complex filter based on search criteria
        filter_query = {}
        
        # Text search across multiple fields
        if "search_text" in search_criteria:
            search_text = search_criteria["search_text"]
            filter_query["$or"] = [
                {"name": {"$regex": search_text, "$options": "i"}},
                {"email": {"$regex": search_text, "$options": "i"}},
                {"primary_contact": {"$regex": search_text, "$options": "i"}}
            ]
        
        # Industry filter
        if "industry" in search_criteria:
            filter_query["industry"] = search_criteria["industry"]
        
        # Company size filter
        if "company_size" in search_criteria:
            filter_query["company_size"] = {"$in": search_criteria["company_size"]}
        
        # Status filter
        if "status" in search_criteria:
            filter_query["status"] = search_criteria["status"]
        else:
            filter_query["status"] = {"$ne": "inactive"}  # Exclude inactive by default
        
        # Date range filter
        if "created_after" in search_criteria:
            filter_query["created_at"] = {"$gte": search_criteria["created_after"]}
        
        # Sales rep filter
        if "assigned_sales_rep" in search_criteria:
            filter_query["assigned_sales_rep"] = search_criteria["assigned_sales_rep"]
        
        # Execute search with pagination
        workflow.add_node("CustomerListNode", "search_customers", {
            "filter": filter_query,
            "order_by": ["-last_order_date", "-created_at"],
            "limit": search_criteria.get("limit", 50),
            "offset": search_criteria.get("offset", 0)
        })
        
        return workflow

# ==============================================================================
# QUOTE GENERATION PATTERNS
# ==============================================================================

class QuoteManagementService:
    """Service class demonstrating quote generation and management patterns"""
    
    @staticmethod
    def generate_quote_workflow(quote_data: Dict[str, Any], line_items: List[Dict], tenant_id: str) -> WorkflowBuilder:
        """Comprehensive quote generation workflow with line items"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Generate unique quote number
        quote_number = f"Q-{datetime.now().strftime('%Y%m%d')}-{datetime.now().microsecond}"
        quote_data["quote_number"] = quote_number
        quote_data["created_date"] = datetime.now()
        quote_data["expiry_date"] = datetime.now() + timedelta(days=30)
        
        # 2. Create quote master record
        workflow.add_node("QuoteCreateNode", "create_quote", quote_data)
        
        # 3. Add line items in bulk for performance
        for i, item in enumerate(line_items):
            item["line_number"] = i + 1
            # Calculate line total
            quantity = item.get("quantity", 1)
            unit_price = item.get("unit_price", 0)
            discount_percent = item.get("discount_percent", 0)
            discount_amount = (unit_price * quantity * discount_percent / 100)
            item["discount_amount"] = discount_amount
            item["line_total"] = (unit_price * quantity) - discount_amount
        
        workflow.add_node("QuoteLineItemBulkCreateNode", "create_line_items", {
            "data": line_items
        })
        workflow.add_connection("create_quote", "id", "create_line_items", "quote_id")
        
        # 4. Calculate quote totals
        subtotal = sum(item["line_total"] for item in line_items)
        tax_rate = quote_data.get("tax_rate", 0.0)
        tax_amount = subtotal * (tax_rate / 100)
        total_amount = subtotal + tax_amount
        
        workflow.add_node("QuoteUpdateNode", "update_totals", {
            "updates": {
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount
            }
        })
        workflow.add_connection("create_quote", "id", "update_totals", "quote_id")
        
        # 5. Log quote creation
        workflow.add_node("ActivityLogCreateNode", "log_quote_creation", {
            "entity_type": "quote",
            "action": "create",
            "user_id": quote_data.get("created_by"),
            "user_name": "Sales Rep",
            "user_role": "sales_rep",
            "ip_address": "127.0.0.1",
            "user_agent": "Sales Assistant",
            "timestamp": datetime.now(),
            "change_summary": f"Quote {quote_number} created for customer {quote_data.get('customer_id')}"
        })
        workflow.add_connection("create_quote", "id", "log_quote_creation", "entity_id")
        
        # 6. Update customer metrics
        workflow.add_node("CustomerUpdateNode", "update_customer_stats", {
            "updates": {
                "total_orders": "total_orders + 1"  # SQL expression for atomic increment
            }
        })
        workflow.add_connection("create_quote", "customer_id", "update_customer_stats", "customer_id")
        
        return workflow
    
    @staticmethod
    def quote_approval_workflow(quote_id: int, approver_id: int, tenant_id: str) -> WorkflowBuilder:
        """Quote approval workflow with business rules"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Get quote details for approval rules
        workflow.add_node("QuoteReadNode", "get_quote", {
            "conditions": {"id": quote_id}
        })
        
        # 2. Check approval requirements based on amount
        # This would typically involve conditional logic based on quote total
        workflow.add_node("QuoteUpdateNode", "approve_quote", {
            "conditions": {"id": quote_id},
            "updates": {
                "status": "approved",
                "approved_by": approver_id,
                "approved_at": datetime.now()
            }
        })
        
        # 3. Log approval activity
        workflow.add_node("ActivityLogCreateNode", "log_approval", {
            "entity_type": "quote",
            "entity_id": str(quote_id),
            "action": "approve",
            "user_id": approver_id,
            "user_name": "Manager",
            "user_role": "sales_manager",
            "ip_address": "127.0.0.1",
            "user_agent": "Sales Assistant",
            "timestamp": datetime.now(),
            "change_summary": f"Quote {quote_id} approved"
        })
        
        # 4. Send notification (would integrate with notification system)
        workflow.add_node("ActivityLogCreateNode", "log_notification", {
            "entity_type": "quote",
            "entity_id": str(quote_id),
            "action": "notify",
            "user_id": approver_id,
            "user_name": "System",
            "user_role": "system",
            "ip_address": "127.0.0.1",
            "user_agent": "DataFlow System",
            "timestamp": datetime.now(),
            "change_summary": "Approval notification sent to customer"
        })
        
        return workflow

# ==============================================================================
# DOCUMENT PROCESSING PATTERNS
# ==============================================================================

class DocumentProcessingService:
    """Service class demonstrating document processing patterns"""
    
    @staticmethod
    def document_upload_workflow(document_data: Dict[str, Any], tenant_id: str) -> WorkflowBuilder:
        """Document upload and AI processing workflow"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Create document record
        document_data["upload_date"] = datetime.now()
        document_data["ai_status"] = "pending"
        workflow.add_node("DocumentCreateNode", "create_document", document_data)
        
        # 2. Queue for AI processing
        workflow.add_node("DocumentProcessingQueueCreateNode", "queue_processing", {
            "processing_type": "extract_and_analyze",
            "priority": 5,
            "ai_model": "gpt-4",
            "queued_at": datetime.now(),
            "processing_config": {
                "extract_entities": True,
                "generate_summary": True,
                "classify_document": True,
                "extract_key_data": True
            }
        })
        workflow.add_connection("create_document", "id", "queue_processing", "document_id")
        
        # 3. Log document upload
        workflow.add_node("ActivityLogCreateNode", "log_upload", {
            "entity_type": "document",
            "action": "upload",
            "user_id": document_data.get("uploaded_by"),
            "user_name": "User",
            "user_role": "sales_rep",
            "ip_address": "127.0.0.1",
            "user_agent": "Sales Assistant",
            "timestamp": datetime.now(),
            "change_summary": f"Document '{document_data.get('name')}' uploaded"
        })
        workflow.add_connection("create_document", "id", "log_upload", "entity_id")
        
        return workflow
    
    @staticmethod
    def document_analysis_results_workflow(
        document_id: int, 
        analysis_results: Dict[str, Any], 
        tenant_id: str
    ) -> WorkflowBuilder:
        """Process AI document analysis results"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Update document with AI results
        workflow.add_node("DocumentUpdateNode", "update_ai_results", {
            "conditions": {"id": document_id},
            "updates": {
                "ai_status": "completed",
                "ai_extracted_data": analysis_results,
                "ai_confidence_score": analysis_results.get("confidence_score", 0.0),
                "summary": analysis_results.get("summary"),
                "key_terms": analysis_results.get("key_terms", [])
            }
        })
        
        # 2. If document is a quote/RFP, create potential quote
        if analysis_results.get("document_type") == "rfp" and analysis_results.get("customer_info"):
            customer_info = analysis_results["customer_info"]
            
            # Create or find customer
            workflow.add_node("CustomerBulkUpsertNode", "upsert_customer", {
                "data": [customer_info],
                "match_fields": ["email"]
            })
            
            # Create draft quote if line items detected
            if analysis_results.get("line_items"):
                workflow.add_node("QuoteCreateNode", "create_draft_quote", {
                    "title": f"Response to {analysis_results.get('rfp_title', 'RFP')}",
                    "status": "draft",
                    "created_date": datetime.now(),
                    "expiry_date": datetime.now() + timedelta(days=30),
                    "created_by": 1,  # System user
                    "subtotal": 0.0,
                    "total_amount": 0.0
                })
                workflow.add_connection("upsert_customer", "id", "create_draft_quote", "customer_id")
        
        # 3. Log analysis completion
        workflow.add_node("ActivityLogCreateNode", "log_analysis", {
            "entity_type": "document",
            "entity_id": str(document_id),
            "action": "analyze",
            "user_id": 1,  # System user
            "user_name": "AI System",
            "user_role": "system",
            "ip_address": "127.0.0.1",
            "user_agent": "AI Document Processor",
            "timestamp": datetime.now(),
            "change_summary": f"Document analysis completed with {analysis_results.get('confidence_score', 0):.1%} confidence"
        })
        
        return workflow

# ==============================================================================
# ERP SYNCHRONIZATION PATTERNS
# ==============================================================================

class ERPSynchronizationService:
    """Service class demonstrating ERP synchronization patterns"""
    
    @staticmethod
    def product_sync_workflow(erp_products: List[Dict[str, Any]], tenant_id: str) -> WorkflowBuilder:
        """Bulk product synchronization from ERP system"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Start sync log
        workflow.add_node("ERPSyncLogCreateNode", "start_sync_log", {
            "sync_type": "products",
            "sync_direction": "inbound",
            "entity_type": "product",
            "erp_system": "SAP",
            "started_at": datetime.now(),
            "status": "running",
            "records_processed": 0,
            "records_successful": 0,
            "records_failed": 0
        })
        
        # 2. Bulk upsert products (insert new, update existing)
        workflow.add_node("ERPProductBulkUpsertNode", "sync_products", {
            "data": erp_products,
            "match_fields": ["erp_product_id"],
            "batch_size": 1000,
            "conflict_resolution": "upsert"
        })
        
        # 3. Update sync log with results
        workflow.add_node("ERPSyncLogUpdateNode", "complete_sync_log", {
            "updates": {
                "completed_at": datetime.now(),
                "status": "completed",
                "records_processed": len(erp_products),
                "records_successful": len(erp_products)  # Simplified for demo
            }
        })
        workflow.add_connection("start_sync_log", "id", "complete_sync_log", "sync_log_id")
        
        # 4. Log synchronization activity
        workflow.add_node("ActivityLogCreateNode", "log_sync", {
            "entity_type": "erp_sync",
            "action": "sync_products",
            "user_id": 1,  # System user
            "user_name": "ERP Sync Service",
            "user_role": "system",
            "ip_address": "127.0.0.1",
            "user_agent": "ERP Synchronizer",
            "timestamp": datetime.now(),
            "change_summary": f"Synchronized {len(erp_products)} products from ERP"
        })
        workflow.add_connection("start_sync_log", "id", "log_sync", "entity_id")
        
        return workflow
    
    @staticmethod
    def quote_to_erp_workflow(quote_id: int, tenant_id: str) -> WorkflowBuilder:
        """Send approved quote to ERP system"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Get quote with line items
        workflow.add_node("QuoteReadNode", "get_quote", {
            "conditions": {"id": quote_id}
        })
        
        workflow.add_node("QuoteLineItemListNode", "get_line_items", {
            "filter": {"quote_id": quote_id},
            "order_by": ["line_number"]
        })
        
        # 2. Format for ERP (this would be custom logic)
        # In practice, this would involve data transformation
        
        # 3. Update quote with ERP sync status
        workflow.add_node("QuoteUpdateNode", "update_sync_status", {
            "conditions": {"id": quote_id},
            "updates": {
                "sync_status": "synced",
                "erp_quote_id": f"ERP-{quote_id}-{datetime.now().strftime('%Y%m%d')}",
                "synced_at": datetime.now()
            }
        })
        
        # 4. Log ERP sync
        workflow.add_node("ActivityLogCreateNode", "log_erp_sync", {
            "entity_type": "quote",
            "entity_id": str(quote_id),
            "action": "erp_sync",
            "user_id": 1,  # System user
            "user_name": "ERP Sync Service",
            "user_role": "system",
            "ip_address": "127.0.0.1",
            "user_agent": "ERP Synchronizer",
            "timestamp": datetime.now(),
            "change_summary": f"Quote {quote_id} synchronized to ERP system"
        })
        
        return workflow

# ==============================================================================
# ANALYTICS AND REPORTING PATTERNS
# ==============================================================================

class AnalyticsService:
    """Service class demonstrating analytics and reporting patterns"""
    
    @staticmethod
    def daily_metrics_workflow(date: datetime, tenant_id: str) -> WorkflowBuilder:
        """Generate daily business metrics"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # 1. Calculate daily quote metrics
        workflow.add_node("QuoteListNode", "daily_quotes", {
            "filter": {
                "created_date": {"$gte": start_of_day, "$lt": end_of_day}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": None,
                        "total_quotes": {"$sum": 1},
                        "total_value": {"$sum": "$total_amount"},
                        "avg_quote_value": {"$avg": "$total_amount"}
                    }
                }
            ]
        })
        
        # 2. Calculate customer acquisition metrics
        workflow.add_node("CustomerListNode", "new_customers", {
            "filter": {
                "created_at": {"$gte": start_of_day, "$lt": end_of_day}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$industry",
                        "count": {"$sum": 1}
                    }
                }
            ]
        })
        
        # 3. Document processing metrics
        workflow.add_node("DocumentListNode", "document_metrics", {
            "filter": {
                "upload_date": {"$gte": start_of_day, "$lt": end_of_day}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$type",
                        "count": {"$sum": 1},
                        "avg_processing_time": {"$avg": "$processing_time"}
                    }
                }
            ]
        })
        
        # 4. Store calculated metrics
        workflow.add_node("BusinessMetricsBulkCreateNode", "store_metrics", {
            "data": []  # This would be populated from aggregation results
        })
        
        return workflow
    
    @staticmethod
    def sales_performance_workflow(user_id: int, period_start: datetime, period_end: datetime, tenant_id: str) -> WorkflowBuilder:
        """Calculate sales representative performance metrics"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Get quotes created by user in period
        workflow.add_node("QuoteListNode", "user_quotes", {
            "filter": {
                "created_by": user_id,
                "created_date": {"$gte": period_start, "$lte": period_end}
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
        
        # 2. Get customer interactions
        workflow.add_node("ActivityLogListNode", "user_activities", {
            "filter": {
                "user_id": user_id,
                "timestamp": {"$gte": period_start, "$lte": period_end},
                "entity_type": {"$in": ["customer", "quote"]}
            },
            "aggregate": [
                {
                    "$group": {
                        "_id": "$action",
                        "count": {"$sum": 1}
                    }
                }
            ]
        })
        
        # 3. Calculate performance metrics
        workflow.add_node("BusinessMetricsCreateNode", "store_performance", {
            "metric_name": "sales_rep_performance",
            "metric_category": "sales",
            "metric_value": 0.0,  # Would be calculated from results
            "metric_unit": "score",
            "period_type": "monthly",
            "period_start": period_start,
            "period_end": period_end,
            "user_id": user_id
        })
        
        return workflow

# ==============================================================================
# TRANSACTION HANDLING PATTERNS
# ==============================================================================

class TransactionService:
    """Service class demonstrating distributed transaction patterns"""
    
    @staticmethod
    def quote_approval_transaction(quote_id: int, approver_id: int, tenant_id: str) -> WorkflowBuilder:
        """Distributed transaction for quote approval process"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Begin distributed transaction
        workflow.add_node("BeginTransactionNode", "begin_txn", {
            "isolation_level": "read_committed",
            "timeout": 30
        })
        
        # 2. Update quote status
        workflow.add_node("QuoteUpdateNode", "approve_quote", {
            "conditions": {"id": quote_id, "status": "pending_approval"},
            "updates": {
                "status": "approved",
                "approved_by": approver_id,
                "approved_at": datetime.now()
            }
        })
        
        # 3. Update customer lifetime value
        workflow.add_node("CustomerUpdateNode", "update_ltv", {
            "conditions": {"id": "quote.customer_id"},  # Dynamic reference
            "updates": {
                "lifetime_value": "lifetime_value + quote.total_amount"
            }
        })
        
        # 4. Create activity log
        workflow.add_node("ActivityLogCreateNode", "log_approval", {
            "entity_type": "quote",
            "entity_id": str(quote_id),
            "action": "approve",
            "user_id": approver_id,
            "timestamp": datetime.now()
        })
        
        # 5. Commit transaction
        workflow.add_node("CommitTransactionNode", "commit_txn", {})
        
        # 6. Rollback on any failure
        workflow.add_node("RollbackTransactionNode", "rollback_txn", {})
        
        # Connect with conditional routing
        workflow.add_connection("begin_txn", "approve_quote")
        workflow.add_connection("approve_quote", "update_ltv", condition="status == 'success'")
        workflow.add_connection("update_ltv", "log_approval", condition="status == 'success'")
        workflow.add_connection("log_approval", "commit_txn", condition="status == 'success'")
        
        # Error handling connections
        workflow.add_connection("approve_quote", "rollback_txn", condition="status == 'failed'")
        workflow.add_connection("update_ltv", "rollback_txn", condition="status == 'failed'")
        workflow.add_connection("log_approval", "rollback_txn", condition="status == 'failed'")
        
        return workflow

# ==============================================================================
# PERFORMANCE OPTIMIZATION PATTERNS
# ==============================================================================

class PerformanceOptimizationService:
    """Service class demonstrating performance optimization patterns"""
    
    @staticmethod
    def bulk_customer_import_workflow(customers_data: List[Dict], tenant_id: str) -> WorkflowBuilder:
        """High-performance bulk customer import"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Validate data in batches
        batch_size = 1000
        for i in range(0, len(customers_data), batch_size):
            batch = customers_data[i:i + batch_size]
            
            # Bulk upsert with conflict resolution
            workflow.add_node("CustomerBulkUpsertNode", f"import_batch_{i}", {
                "data": batch,
                "match_fields": ["email"],
                "batch_size": batch_size,
                "conflict_resolution": "upsert",
                "return_ids": False  # Optimize for performance
            })
        
        # 2. Update import metrics
        workflow.add_node("BusinessMetricsCreateNode", "import_metrics", {
            "metric_name": "customer_import_count",
            "metric_category": "system",
            "metric_value": len(customers_data),
            "metric_unit": "count",
            "period_type": "daily",
            "period_start": datetime.now(),
            "period_end": datetime.now()
        })
        
        return workflow
    
    @staticmethod
    def cached_product_search_workflow(search_params: Dict, tenant_id: str) -> WorkflowBuilder:
        """Product search with intelligent caching"""
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # Generate cache key based on search parameters
        cache_key = f"product_search_{hash(str(sorted(search_params.items())))}"
        
        # Search with caching enabled
        workflow.add_node("ERPProductListNode", "search_products", {
            "filter": search_params,
            "order_by": ["name"],
            "limit": 100,
            "cache_key": cache_key,
            "cache_ttl": 300,  # 5 minutes
            "cache_invalidation": ["product_create", "product_update", "product_delete"]
        })
        
        return workflow

# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

def demo_usage_patterns():
    """Demonstrate comprehensive DataFlow usage patterns"""
    runtime = LocalRuntime()
    
    # 1. Customer Management Example
    print("=== Customer Management Demo ===")
    customer_service = CustomerManagementService()
    
    customer_workflow = customer_service.create_customer_workflow({
        "name": "Acme Corporation",
        "type": "business",
        "industry": "Manufacturing",
        "primary_contact": "John Smith",
        "email": "john.smith@acme.com",
        "phone": "+1-555-0123",
        "billing_address": {
            "street": "123 Business Ave",
            "city": "Businessville",
            "state": "CA",
            "zip": "90210",
            "country": "USA"
        },
        "assigned_sales_rep": 1,
        "status": "active"
    }, tenant_id="company_123")
    
    results, run_id = runtime.execute(customer_workflow.build())
    print(f"Customer created with ID: {results.get('create_customer', {}).get('id', 'Unknown')}")
    
    # 2. Quote Generation Example
    print("\n=== Quote Generation Demo ===")
    quote_service = QuoteManagementService()
    
    quote_workflow = quote_service.generate_quote_workflow({
        "customer_id": 1,
        "title": "Q1 Equipment Quote",
        "description": "Quarterly equipment order",
        "created_by": 1,
        "currency": "USD",
        "tax_rate": 8.5
    }, [
        {
            "product_name": "Industrial Pump Model A",
            "description": "High-capacity industrial pump",
            "quantity": 2,
            "unit_price": 1250.00,
            "discount_percent": 5.0,
            "category": "Equipment"
        },
        {
            "product_name": "Pump Installation Kit",
            "description": "Installation hardware and fittings",
            "quantity": 2,
            "unit_price": 150.00,
            "discount_percent": 0.0,
            "category": "Accessories"
        }
    ], tenant_id="company_123")
    
    results, run_id = runtime.execute(quote_workflow.build())
    print(f"Quote created with ID: {results.get('create_quote', {}).get('id', 'Unknown')}")
    
    # 3. Document Processing Example
    print("\n=== Document Processing Demo ===")
    doc_service = DocumentProcessingService()
    
    doc_workflow = doc_service.document_upload_workflow({
        "name": "RFP_Marina_Corp_2025.pdf",
        "type": "rfp",
        "category": "inbound",
        "file_path": "/uploads/rfp_marina_corp_2025.pdf",
        "file_size": 2048576,
        "mime_type": "application/pdf",
        "customer_id": 1,
        "uploaded_by": 1,
        "security_level": "internal"
    }, tenant_id="company_123")
    
    results, run_id = runtime.execute(doc_workflow.build())
    print(f"Document uploaded with ID: {results.get('create_document', {}).get('id', 'Unknown')}")
    
    # 4. Analytics Example
    print("\n=== Analytics Demo ===")
    analytics_service = AnalyticsService()
    
    metrics_workflow = analytics_service.daily_metrics_workflow(
        datetime.now(), 
        tenant_id="company_123"
    )
    
    results, run_id = runtime.execute(metrics_workflow.build())
    print("Daily metrics calculated and stored")
    
    print("\n=== All Patterns Demonstrated Successfully ===")

if __name__ == "__main__":
    demo_usage_patterns()