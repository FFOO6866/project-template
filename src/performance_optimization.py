"""
Performance Optimization and Transaction Handling for DataFlow Sales Assistant
=============================================================================

This module demonstrates advanced performance optimization techniques including:
- Connection pooling and database optimization
- Query optimization patterns
- Bulk operation strategies
- Distributed transaction handling
- Caching strategies
- Real-time performance monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataflow import DataFlow
from dataflow_models import db
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
import asyncio
import time

# ==============================================================================
# CONNECTION POOLING AND DATABASE OPTIMIZATION
# ==============================================================================

class DatabaseOptimizer:
    """Advanced database optimization utilities"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def optimize_connection_pooling(self, tenant_load_profile: Dict[str, int]) -> Dict[str, Any]:
        """Optimize connection pooling based on tenant load profiles"""
        
        workflow = WorkflowBuilder()
        
        # Calculate optimal pool sizes based on tenant activity
        total_expected_connections = sum(tenant_load_profile.values())
        
        # Configure adaptive connection pooling
        pool_config = {
            "base_pool_size": max(10, total_expected_connections // 4),
            "max_pool_size": max(50, total_expected_connections),
            "pool_overflow": max(20, total_expected_connections // 2),
            "pool_recycle_seconds": 3600,
            "pool_pre_ping": True,
            "pool_timeout": 30
        }
        
        # Apply connection pool optimization
        workflow.add_node("OptimizeConnectionPoolNode", "optimize_pool", pool_config)
        
        # Monitor connection usage
        workflow.add_node("MonitorConnectionPoolNode", "monitor_pool", {
            "metrics_to_track": [
                "active_connections",
                "idle_connections",
                "pool_utilization",
                "connection_wait_time",
                "connection_errors"
            ],
            "monitoring_interval_seconds": 60
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "pool_configuration": pool_config,
            "optimization_status": results.get("optimize_pool", {}).get("status"),
            "monitoring_enabled": results.get("monitor_pool", {}).get("status") == "success"
        }
    
    def create_performance_indexes(self, tenant_id: str) -> bool:
        """Create performance-optimized indexes for sales assistant workloads"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # High-performance indexes for common query patterns
        performance_indexes = [
            {
                "name": "idx_customers_search_composite",
                "table": "customers",
                "columns": ["tenant_id", "status", "industry", "name"],
                "type": "btree",
                "purpose": "Customer search optimization"
            },
            {
                "name": "idx_quotes_dashboard_composite",
                "table": "quotes",
                "columns": ["tenant_id", "status", "created_date", "total_amount"],
                "type": "btree",
                "purpose": "Quote dashboard queries"
            },
            {
                "name": "idx_documents_ai_processing",
                "table": "documents",
                "columns": ["tenant_id", "ai_status", "upload_date"],
                "type": "btree",
                "purpose": "AI processing queue optimization"
            },
            {
                "name": "idx_activity_logs_audit",
                "table": "activity_logs",
                "columns": ["tenant_id", "entity_type", "timestamp"],
                "type": "btree",
                "purpose": "Audit trail queries"
            },
            {
                "name": "idx_erp_products_search_gin",
                "table": "erp_products",
                "columns": ["to_tsvector('english', name || ' ' || description)"],
                "type": "gin",
                "purpose": "Full-text product search"
            }
        ]
        
        for i, index in enumerate(performance_indexes):
            if index["type"] == "gin":
                # GIN index for full-text search
                sql = f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}
                ON {index['table']} USING gin ({index['columns'][0]})
                WHERE tenant_id = {tenant_id};
                """
            else:
                # Standard B-tree index
                sql = f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}
                ON {index['table']} ({', '.join(index['columns'])})
                WHERE tenant_id = {tenant_id};
                """
            
            workflow.add_node("ExecuteSQLNode", f"create_index_{i}", {
                "sql": sql,
                "execute_as": "admin",
                "timeout": 600,  # 10 minutes for concurrent index creation
                "description": index["purpose"]
            })
        
        results, run_id = self.runtime.execute(workflow.build())
        return all(result.get("status") == "success" for result in results.values())
    
    def analyze_query_performance(self, tenant_id: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze query performance and provide optimization recommendations"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # Get slow query statistics
        workflow.add_node("AnalyzeSlowQueriesNode", "slow_queries", {
            "tenant_id": tenant_id,
            "time_period_hours": hours,
            "min_execution_time_ms": 1000,  # Queries slower than 1 second
            "include_query_plans": True
        })
        
        # Analyze index usage
        workflow.add_node("AnalyzeIndexUsageNode", "index_usage", {
            "tenant_id": tenant_id,
            "include_unused_indexes": True,
            "include_missing_indexes": True
        })
        
        # Check table statistics
        workflow.add_node("AnalyzeTableStatsNode", "table_stats", {
            "tenant_id": tenant_id,
            "tables": ["customers", "quotes", "documents", "erp_products"],
            "include_size_stats": True,
            "include_fragmentation": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "analysis_period_hours": hours,
            "slow_queries": results.get("slow_queries", {}).get("result", []),
            "index_analysis": results.get("index_usage", {}).get("result", {}),
            "table_statistics": results.get("table_stats", {}).get("result", {}),
            "recommendations": self._generate_performance_recommendations(results),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _generate_performance_recommendations(self, analysis_results: Dict) -> List[Dict[str, str]]:
        """Generate performance optimization recommendations based on analysis"""
        
        recommendations = []
        
        # Analyze slow queries
        slow_queries = analysis_results.get("slow_queries", {}).get("result", [])
        if slow_queries:
            recommendations.append({
                "type": "slow_queries",
                "priority": "high",
                "description": f"Found {len(slow_queries)} slow queries",
                "action": "Review and optimize slow queries, consider adding indexes"
            })
        
        # Analyze index usage
        index_usage = analysis_results.get("index_usage", {}).get("result", {})
        unused_indexes = index_usage.get("unused_indexes", [])
        if unused_indexes:
            recommendations.append({
                "type": "unused_indexes",
                "priority": "medium",
                "description": f"Found {len(unused_indexes)} unused indexes",
                "action": "Consider dropping unused indexes to improve write performance"
            })
        
        missing_indexes = index_usage.get("missing_indexes", [])
        if missing_indexes:
            recommendations.append({
                "type": "missing_indexes",
                "priority": "high",
                "description": f"Identified {len(missing_indexes)} beneficial indexes",
                "action": "Create recommended indexes to improve query performance"
            })
        
        return recommendations

# ==============================================================================
# BULK OPERATION STRATEGIES
# ==============================================================================

class BulkOperationOptimizer:
    """Advanced bulk operation optimization utilities"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def optimized_bulk_customer_import(
        self, 
        customers: List[Dict[str, Any]], 
        tenant_id: str,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """High-performance bulk customer import with optimization"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        start_time = time.time()
        
        # 1. Validate and prepare data
        workflow.add_node("ValidateDataNode", "validate_customers", {
            "data": customers,
            "validation_rules": {
                "required_fields": ["name", "email", "primary_contact"],
                "email_validation": True,
                "duplicate_detection": "email",
                "data_quality_threshold": 0.95
            }
        })
        
        # 2. Pre-process data for optimization
        workflow.add_node("PreprocessDataNode", "preprocess_customers", {
            "operations": [
                "normalize_phone_numbers",
                "standardize_addresses",
                "extract_company_domains",
                "calculate_data_quality_scores"
            ]
        })
        
        # 3. Bulk upsert in optimized batches
        total_batches = (len(customers) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(customers))
            batch_data = customers[start_idx:end_idx]
            
            workflow.add_node("CustomerBulkUpsertNode", f"import_batch_{batch_num}", {
                "data": batch_data,
                "match_fields": ["email"],
                "batch_size": batch_size,
                "conflict_resolution": "upsert",
                "return_ids": False,  # Optimize for performance
                "disable_triggers": True,  # Disable for bulk import
                "use_copy_mode": True  # Use COPY for maximum performance
            })
        
        # 4. Re-enable triggers and update statistics
        workflow.add_node("OptimizationCleanupNode", "cleanup", {
            "operations": [
                "enable_triggers",
                "update_table_statistics",
                "rebuild_indexes_if_needed"
            ]
        })
        
        # 5. Generate import metrics
        workflow.add_node("BusinessMetricsCreateNode", "import_metrics", {
            "metric_name": "bulk_customer_import",
            "metric_category": "performance",
            "metric_value": len(customers),
            "metric_unit": "records",
            "period_type": "operation",
            "period_start": datetime.fromtimestamp(start_time),
            "period_end": datetime.now(),
            "metadata": {
                "batch_size": batch_size,
                "total_batches": total_batches,
                "optimization_enabled": True
            }
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        end_time = time.time()
        
        return {
            "total_records": len(customers),
            "batch_size": batch_size,
            "total_batches": total_batches,
            "processing_time_seconds": end_time - start_time,
            "records_per_second": len(customers) / (end_time - start_time),
            "validation_results": results.get("validate_customers", {}),
            "import_status": "success" if all(
                r.get("status") == "success" for r in results.values()
            ) else "partial_success"
        }
    
    def optimized_bulk_quote_processing(
        self, 
        quotes_with_line_items: List[Dict[str, Any]], 
        tenant_id: str
    ) -> Dict[str, Any]:
        """Process multiple quotes with line items in bulk for maximum performance"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        start_time = time.time()
        
        # 1. Extract and prepare quote master data
        quote_masters = []
        all_line_items = []
        
        for i, quote_data in enumerate(quotes_with_line_items):
            quote_master = {k: v for k, v in quote_data.items() if k != "line_items"}
            quote_master["quote_number"] = f"BULK-{datetime.now().strftime('%Y%m%d')}-{i:04d}"
            quote_master["created_date"] = datetime.now()
            quote_master["expiry_date"] = datetime.now() + timedelta(days=30)
            quote_masters.append(quote_master)
            
            # Prepare line items with temporary quote reference
            for j, line_item in enumerate(quote_data.get("line_items", [])):
                line_item["quote_index"] = i  # Temporary reference
                line_item["line_number"] = j + 1
                # Calculate line totals
                quantity = line_item.get("quantity", 1)
                unit_price = line_item.get("unit_price", 0)
                discount_percent = line_item.get("discount_percent", 0)
                discount_amount = (unit_price * quantity * discount_percent / 100)
                line_item["discount_amount"] = discount_amount
                line_item["line_total"] = (unit_price * quantity) - discount_amount
                all_line_items.append(line_item)
        
        # 2. Bulk create quote masters
        workflow.add_node("QuoteBulkCreateNode", "create_quotes", {
            "data": quote_masters,
            "batch_size": 500,
            "return_ids": True,  # Need IDs for line items
            "use_copy_mode": True
        })
        
        # 3. Update line items with actual quote IDs (would need custom logic)
        workflow.add_node("ProcessLineItemReferencesNode", "update_line_item_refs", {
            "line_items": all_line_items,
            "quote_id_mapping": "from_previous_step"  # Dynamic reference
        })
        
        # 4. Bulk create line items
        workflow.add_node("QuoteLineItemBulkCreateNode", "create_line_items", {
            "data": all_line_items,
            "batch_size": 2000,
            "use_copy_mode": True,
            "disable_triggers": True
        })
        
        # 5. Bulk update quote totals
        workflow.add_node("BulkUpdateQuoteTotalsNode", "update_totals", {
            "calculate_from_line_items": True,
            "batch_size": 500
        })
        
        # 6. Generate performance metrics
        total_records = len(quote_masters) + len(all_line_items)
        workflow.add_node("BusinessMetricsCreateNode", "bulk_quote_metrics", {
            "metric_name": "bulk_quote_processing",
            "metric_category": "performance",
            "metric_value": total_records,
            "metric_unit": "records",
            "period_type": "operation",
            "period_start": datetime.fromtimestamp(start_time),
            "period_end": datetime.now(),
            "metadata": {
                "quotes_processed": len(quote_masters),
                "line_items_processed": len(all_line_items),
                "optimization_enabled": True
            }
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        end_time = time.time()
        
        return {
            "quotes_processed": len(quote_masters),
            "line_items_processed": len(all_line_items),
            "total_records": total_records,
            "processing_time_seconds": end_time - start_time,
            "records_per_second": total_records / (end_time - start_time),
            "quotes_created": len(results.get("create_quotes", {}).get("result", [])),
            "processing_status": "success"
        }

# ==============================================================================
# DISTRIBUTED TRANSACTION HANDLING
# ==============================================================================

class DistributedTransactionManager:
    """Advanced distributed transaction handling utilities"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def quote_approval_saga(
        self, 
        quote_id: int, 
        approver_id: int, 
        tenant_id: str
    ) -> Dict[str, Any]:
        """Implement Saga pattern for quote approval process"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Begin Saga transaction
        workflow.add_node("BeginSagaNode", "begin_saga", {
            "saga_id": f"quote_approval_{quote_id}_{datetime.now().timestamp()}",
            "timeout_seconds": 300,  # 5 minutes
            "isolation_level": "read_committed"
        })
        
        # 2. Step 1: Validate quote status
        workflow.add_node("QuoteReadNode", "validate_quote", {
            "conditions": {"id": quote_id, "status": {"$in": ["pending_approval", "draft"]}}
        })
        
        # Compensation: No rollback needed for read operation
        
        # 3. Step 2: Check approval authority
        workflow.add_node("ValidateApprovalAuthorityNode", "check_authority", {
            "quote_id": quote_id,
            "approver_id": approver_id,
            "required_authority_level": "quote_approval"
        })
        
        # 4. Step 3: Update quote status
        workflow.add_node("QuoteUpdateNode", "approve_quote", {
            "conditions": {"id": quote_id},
            "updates": {
                "status": "approved",
                "approved_by": approver_id,
                "approved_at": datetime.now(),
                "version": "version + 1"  # Optimistic locking
            }
        })
        
        # Compensation: Revert quote status
        workflow.add_node("QuoteUpdateNode", "rollback_quote_approval", {
            "conditions": {"id": quote_id},
            "updates": {
                "status": "pending_approval",
                "approved_by": None,
                "approved_at": None
            },
            "execute_on": "compensation"
        })
        
        # 5. Step 4: Update customer lifetime value
        workflow.add_node("UpdateCustomerLTVNode", "update_ltv", {
            "quote_id": quote_id,
            "operation": "add_quote_value"
        })
        
        # Compensation: Subtract quote value from LTV
        workflow.add_node("UpdateCustomerLTVNode", "rollback_ltv", {
            "quote_id": quote_id,
            "operation": "subtract_quote_value",
            "execute_on": "compensation"
        })
        
        # 6. Step 5: Create approval activity log
        workflow.add_node("ActivityLogCreateNode", "log_approval", {
            "entity_type": "quote",
            "entity_id": str(quote_id),
            "action": "approve",
            "user_id": approver_id,
            "timestamp": datetime.now(),
            "change_summary": f"Quote {quote_id} approved"
        })
        
        # Compensation: Create rollback activity log
        workflow.add_node("ActivityLogCreateNode", "log_rollback", {
            "entity_type": "quote",
            "entity_id": str(quote_id),
            "action": "rollback_approval",
            "user_id": approver_id,
            "timestamp": datetime.now(),
            "change_summary": f"Quote {quote_id} approval rolled back",
            "execute_on": "compensation"
        })
        
        # 7. Step 6: Send approval notification
        workflow.add_node("SendNotificationNode", "send_notification", {
            "notification_type": "quote_approved",
            "quote_id": quote_id,
            "recipients": ["customer", "sales_rep"],
            "template": "quote_approval_notification"
        })
        
        # 8. Commit Saga
        workflow.add_node("CommitSagaNode", "commit_saga", {})
        
        # 9. Saga failure handler
        workflow.add_node("HandleSagaFailureNode", "handle_failure", {
            "execute_compensations": True,
            "notify_failure": True,
            "execute_on": "failure"
        })
        
        # Define Saga step connections with compensation chains
        workflow.add_connection("begin_saga", "validate_quote")
        workflow.add_connection("validate_quote", "check_authority", condition="status == 'success'")
        workflow.add_connection("check_authority", "approve_quote", condition="status == 'success'")
        workflow.add_connection("approve_quote", "update_ltv", condition="status == 'success'")
        workflow.add_connection("update_ltv", "log_approval", condition="status == 'success'")
        workflow.add_connection("log_approval", "send_notification", condition="status == 'success'")
        workflow.add_connection("send_notification", "commit_saga", condition="status == 'success'")
        
        # Failure and compensation routing
        failure_steps = ["validate_quote", "check_authority", "approve_quote", "update_ltv", "log_approval", "send_notification"]
        for step in failure_steps:
            workflow.add_connection(step, "handle_failure", condition="status == 'failed'")
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "saga_id": results.get("begin_saga", {}).get("saga_id"),
            "quote_id": quote_id,
            "approver_id": approver_id,
            "saga_status": results.get("commit_saga", {}).get("status", "failed"),
            "compensation_executed": results.get("handle_failure", {}).get("compensations_executed", False),
            "approval_successful": results.get("approve_quote", {}).get("status") == "success",
            "completed_at": datetime.now().isoformat()
        }
    
    def erp_synchronization_transaction(
        self, 
        sync_operations: List[Dict[str, Any]], 
        tenant_id: str
    ) -> Dict[str, Any]:
        """Handle ERP synchronization with distributed transaction support"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Begin distributed transaction across DataFlow and ERP
        workflow.add_node("BeginDistributedTransactionNode", "begin_txn", {
            "transaction_id": f"erp_sync_{tenant_id}_{datetime.now().timestamp()}",
            "participants": ["dataflow_db", "erp_system"],
            "timeout_seconds": 600,  # 10 minutes
            "isolation_level": "serializable"
        })
        
        # 2. Prepare phase - validate all operations
        for i, operation in enumerate(sync_operations):
            workflow.add_node("ValidateSyncOperationNode", f"validate_op_{i}", {
                "operation_type": operation["type"],
                "operation_data": operation["data"],
                "validation_rules": operation.get("validation_rules", {})
            })
        
        # 3. Execute phase - perform all operations
        for i, operation in enumerate(sync_operations):
            if operation["type"] == "product_sync":
                workflow.add_node("ERPProductBulkUpsertNode", f"sync_products_{i}", {
                    "data": operation["data"],
                    "match_fields": ["erp_product_id"],
                    "batch_size": 500
                })
            elif operation["type"] == "customer_sync":
                workflow.add_node("CustomerBulkUpsertNode", f"sync_customers_{i}", {
                    "data": operation["data"],
                    "match_fields": ["email"],
                    "batch_size": 200
                })
            elif operation["type"] == "quote_export":
                workflow.add_node("ExportQuoteToERPNode", f"export_quote_{i}", {
                    "quote_id": operation["quote_id"],
                    "erp_system": operation["erp_system"]
                })
        
        # 4. Log synchronization operations
        workflow.add_node("ERPSyncLogCreateNode", "log_sync", {
            "sync_type": "distributed_transaction",
            "sync_direction": "bidirectional",
            "entity_type": "multiple",
            "erp_system": sync_operations[0].get("erp_system", "unknown"),
            "started_at": datetime.now(),
            "records_processed": sum(len(op.get("data", [])) for op in sync_operations)
        })
        
        # 5. Commit distributed transaction
        workflow.add_node("CommitDistributedTransactionNode", "commit_txn", {
            "verify_all_participants": True
        })
        
        # 6. Rollback handler
        workflow.add_node("RollbackDistributedTransactionNode", "rollback_txn", {
            "rollback_all_participants": True,
            "execute_on": "failure"
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "transaction_id": results.get("begin_txn", {}).get("transaction_id"),
            "operations_count": len(sync_operations),
            "transaction_status": results.get("commit_txn", {}).get("status", "failed"),
            "rollback_executed": results.get("rollback_txn", {}).get("status") == "success",
            "sync_log_id": results.get("log_sync", {}).get("id"),
            "completed_at": datetime.now().isoformat()
        }

# ==============================================================================
# CACHING STRATEGIES
# ==============================================================================

class CachingOptimizer:
    """Advanced caching optimization utilities"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def implement_multi_level_caching(self, tenant_id: str) -> Dict[str, Any]:
        """Implement multi-level caching strategy for sales assistant"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Configure L1 Cache (Application Level)
        workflow.add_node("ConfigureCacheLayerNode", "l1_cache", {
            "cache_level": "L1",
            "cache_type": "memory",
            "max_size_mb": 256,
            "default_ttl_seconds": 300,  # 5 minutes
            "cache_policies": {
                "customer_profiles": {"ttl": 1800, "max_items": 1000},
                "product_catalog": {"ttl": 3600, "max_items": 5000},
                "quote_templates": {"ttl": 7200, "max_items": 500},
                "user_preferences": {"ttl": 1800, "max_items": 200}
            }
        })
        
        # 2. Configure L2 Cache (Redis)
        workflow.add_node("ConfigureCacheLayerNode", "l2_cache", {
            "cache_level": "L2",
            "cache_type": "redis",
            "max_size_mb": 1024,
            "default_ttl_seconds": 3600,  # 1 hour
            "cache_policies": {
                "search_results": {"ttl": 900, "compression": True},
                "aggregated_metrics": {"ttl": 1800, "compression": True},
                "document_metadata": {"ttl": 7200, "compression": False},
                "erp_product_data": {"ttl": 3600, "compression": True}
            }
        })
        
        # 3. Configure L3 Cache (Database Query Result Cache)
        workflow.add_node("ConfigureCacheLayerNode", "l3_cache", {
            "cache_level": "L3",
            "cache_type": "query_result",
            "default_ttl_seconds": 7200,  # 2 hours
            "cache_policies": {
                "complex_analytics": {"ttl": 14400},  # 4 hours
                "reference_data": {"ttl": 86400},     # 24 hours
                "audit_queries": {"ttl": 3600}        # 1 hour
            }
        })
        
        # 4. Set up cache invalidation strategies
        workflow.add_node("ConfigureCacheInvalidationNode", "cache_invalidation", {
            "invalidation_strategies": {
                "customer_data": {
                    "triggers": ["customer_update", "customer_delete"],
                    "pattern": "customer:*:{customer_id}",
                    "cascade_invalidation": ["quotes:customer:{customer_id}"]
                },
                "product_data": {
                    "triggers": ["erp_product_update", "erp_sync_complete"],
                    "pattern": "product:*",
                    "batch_invalidation": True
                },
                "quote_data": {
                    "triggers": ["quote_update", "quote_approve", "quote_delete"],
                    "pattern": "quote:*:{quote_id}",
                    "cascade_invalidation": ["customer:*:{customer_id}"]
                }
            }
        })
        
        # 5. Enable cache warming for frequently accessed data
        workflow.add_node("ConfigureCacheWarmingNode", "cache_warming", {
            "warming_schedules": {
                "product_catalog": {
                    "schedule": "0 */6 * * *",  # Every 6 hours
                    "query": "ERPProductListNode",
                    "filter": {"stock_status": "available"},
                    "warm_l1": True,
                    "warm_l2": True
                },
                "active_customers": {
                    "schedule": "0 0 * * *",  # Daily
                    "query": "CustomerListNode",
                    "filter": {"status": "active"},
                    "warm_l1": True,
                    "warm_l2": True
                },
                "popular_templates": {
                    "schedule": "0 */12 * * *",  # Every 12 hours
                    "query": "QuoteTemplateListNode",
                    "filter": {"usage_count": {"$gt": 10}},
                    "warm_l1": True,
                    "warm_l2": True
                }
            }
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "l1_cache_configured": results.get("l1_cache", {}).get("status") == "success",
            "l2_cache_configured": results.get("l2_cache", {}).get("status") == "success",
            "l3_cache_configured": results.get("l3_cache", {}).get("status") == "success",
            "invalidation_configured": results.get("cache_invalidation", {}).get("status") == "success",
            "cache_warming_enabled": results.get("cache_warming", {}).get("status") == "success",
            "configuration_completed_at": datetime.now().isoformat()
        }
    
    def intelligent_cache_preloading(self, tenant_id: str, user_id: int) -> Dict[str, Any]:
        """Implement intelligent cache preloading based on user behavior patterns"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Analyze user behavior patterns
        workflow.add_node("AnalyzeUserBehaviorNode", "behavior_analysis", {
            "user_id": user_id,
            "analysis_period_days": 30,
            "include_patterns": [
                "frequently_accessed_customers",
                "common_search_terms",
                "preferred_product_categories",
                "typical_workflow_patterns"
            ]
        })
        
        # 2. Generate personalized cache preloading strategy
        workflow.add_node("GeneratePreloadingStrategyNode", "preloading_strategy", {
            "user_id": user_id,
            "based_on_behavior": True,
            "preload_categories": [
                "customers", "products", "quotes", "templates", "documents"
            ]
        })
        
        # 3. Execute intelligent preloading
        workflow.add_node("ExecuteIntelligentPreloadingNode", "execute_preloading", {
            "user_id": user_id,
            "strategy": "from_previous_step",
            "max_preload_items": 1000,
            "max_preload_size_mb": 100
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "behavior_patterns": results.get("behavior_analysis", {}).get("result", {}),
            "preloading_strategy": results.get("preloading_strategy", {}).get("result", {}),
            "preloading_executed": results.get("execute_preloading", {}).get("status") == "success",
            "items_preloaded": results.get("execute_preloading", {}).get("items_count", 0),
            "cache_size_mb": results.get("execute_preloading", {}).get("cache_size_mb", 0),
            "completed_at": datetime.now().isoformat()
        }

# ==============================================================================
# REAL-TIME PERFORMANCE MONITORING
# ==============================================================================

class PerformanceMonitor:
    """Real-time performance monitoring utilities"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def setup_real_time_monitoring(self, tenant_id: str) -> Dict[str, Any]:
        """Setup comprehensive real-time performance monitoring"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Database performance monitoring
        workflow.add_node("SetupDBMonitoringNode", "db_monitoring", {
            "metrics": [
                "query_response_time",
                "connection_pool_utilization",
                "active_queries_count",
                "slow_query_detection",
                "deadlock_detection",
                "table_scan_frequency"
            ],
            "collection_interval_seconds": 30,
            "alert_thresholds": {
                "slow_query_ms": 2000,
                "connection_pool_threshold": 0.8,
                "deadlock_count": 1
            }
        })
        
        # 2. Application performance monitoring
        workflow.add_node("SetupAppMonitoringNode", "app_monitoring", {
            "metrics": [
                "workflow_execution_time",
                "node_performance",
                "memory_usage",
                "cache_hit_rates",
                "api_response_times"
            ],
            "collection_interval_seconds": 15,
            "alert_thresholds": {
                "workflow_timeout_ms": 30000,
                "memory_usage_mb": 1024,
                "cache_hit_rate": 0.8
            }
        })
        
        # 3. Business metrics monitoring
        workflow.add_node("SetupBusinessMonitoringNode", "business_monitoring", {
            "metrics": [
                "quotes_per_hour",
                "document_processing_rate",
                "user_activity_levels",
                "system_utilization"
            ],
            "collection_interval_seconds": 60,
            "trending_analysis": True
        })
        
        # 4. Setup alerting system
        workflow.add_node("SetupAlertingNode", "alerting_system", {
            "alert_channels": ["email", "webhook", "dashboard"],
            "alert_rules": [
                {
                    "name": "high_response_time",
                    "condition": "avg_response_time > 2000",
                    "severity": "warning",
                    "notification_interval_minutes": 5
                },
                {
                    "name": "system_overload",
                    "condition": "connection_pool_usage > 0.9 AND memory_usage > 0.8",
                    "severity": "critical",
                    "notification_interval_minutes": 1
                },
                {
                    "name": "low_performance",
                    "condition": "cache_hit_rate < 0.5",
                    "severity": "warning",
                    "notification_interval_minutes": 15
                }
            ]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "db_monitoring_enabled": results.get("db_monitoring", {}).get("status") == "success",
            "app_monitoring_enabled": results.get("app_monitoring", {}).get("status") == "success",
            "business_monitoring_enabled": results.get("business_monitoring", {}).get("status") == "success",
            "alerting_configured": results.get("alerting_system", {}).get("status") == "success",
            "monitoring_started_at": datetime.now().isoformat()
        }
    
    def get_performance_dashboard_data(self, tenant_id: str) -> Dict[str, Any]:
        """Get real-time performance dashboard data"""
        
        workflow = WorkflowBuilder()
        workflow.metadata["tenant_id"] = tenant_id
        
        # 1. Current system metrics
        workflow.add_node("GetCurrentMetricsNode", "current_metrics", {
            "metrics": [
                "database_connections",
                "memory_usage",
                "cpu_utilization",
                "cache_statistics",
                "active_workflows"
            ]
        })
        
        # 2. Performance trends (last 24 hours)
        workflow.add_node("GetPerformanceTrendsNode", "performance_trends", {
            "time_range_hours": 24,
            "metrics": [
                "average_response_time",
                "queries_per_minute",
                "error_rate",
                "throughput"
            ],
            "aggregation_interval_minutes": 15
        })
        
        # 3. Top performing/slow operations
        workflow.add_node("GetTopOperationsNode", "top_operations", {
            "time_range_hours": 1,
            "include_top_performers": 10,
            "include_slow_operations": 10
        })
        
        # 4. Current alerts and issues
        workflow.add_node("GetActiveAlertsNode", "active_alerts", {
            "include_resolved_minutes": 60
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "current_metrics": results.get("current_metrics", {}).get("result", {}),
            "performance_trends": results.get("performance_trends", {}).get("result", []),
            "top_operations": results.get("top_operations", {}).get("result", {}),
            "active_alerts": results.get("active_alerts", {}).get("result", [])
        }

# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

def demo_performance_optimization():
    """Demonstrate comprehensive performance optimization techniques"""
    
    print("=== DataFlow Performance Optimization Demo ===")
    
    # Initialize optimizers
    db_optimizer = DatabaseOptimizer(db)
    bulk_optimizer = BulkOperationOptimizer(db)
    txn_manager = DistributedTransactionManager(db)
    cache_optimizer = CachingOptimizer(db)
    perf_monitor = PerformanceMonitor(db)
    
    tenant_id = "performance_demo_tenant"
    
    # 1. Database Optimization
    print("\n--- Database Optimization ---")
    pool_optimization = db_optimizer.optimize_connection_pooling({
        "tenant_1": 20,
        "tenant_2": 15,
        "tenant_3": 25
    })
    print(f"Connection pool optimized: {pool_optimization['optimization_status']}")
    
    index_creation = db_optimizer.create_performance_indexes(tenant_id)
    print(f"Performance indexes created: {index_creation}")
    
    # 2. Bulk Operations
    print("\n--- Bulk Operations Optimization ---")
    sample_customers = [
        {
            "name": f"Customer {i}",
            "email": f"customer{i}@example.com",
            "primary_contact": f"Contact {i}",
            "type": "business",
            "industry": "Technology" if i % 2 == 0 else "Manufacturing"
        }
        for i in range(1000)  # 1000 customers for demo
    ]
    
    bulk_result = bulk_optimizer.optimized_bulk_customer_import(
        sample_customers, tenant_id, batch_size=200
    )
    print(f"Bulk import: {bulk_result['records_per_second']:.0f} records/second")
    
    # 3. Caching Strategy
    print("\n--- Multi-Level Caching ---")
    cache_setup = cache_optimizer.implement_multi_level_caching(tenant_id)
    print(f"Multi-level caching configured: {cache_setup['l1_cache_configured']}")
    
    # 4. Performance Monitoring
    print("\n--- Real-Time Monitoring ---")
    monitoring_setup = perf_monitor.setup_real_time_monitoring(tenant_id)
    print(f"Performance monitoring enabled: {monitoring_setup['db_monitoring_enabled']}")
    
    # 5. Distributed Transaction Demo
    print("\n--- Distributed Transaction ---")
    saga_result = txn_manager.quote_approval_saga(
        quote_id=1, approver_id=1, tenant_id=tenant_id
    )
    print(f"Saga transaction: {saga_result['saga_status']}")
    
    print("\n=== Performance Optimization Demo Complete ===")

if __name__ == "__main__":
    demo_performance_optimization()