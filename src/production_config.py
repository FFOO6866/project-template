"""
Production Configuration and Best Practices for DataFlow Sales Assistant
=======================================================================

This module provides comprehensive production configuration including:
- Environment-specific configurations
- Security best practices
- Monitoring and alerting setup
- Backup and disaster recovery
- Performance tuning
- Compliance and audit configuration
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataflow import DataFlow, DataFlowConfig, Environment
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# ==============================================================================
# PRODUCTION CONFIGURATION CLASSES
# ==============================================================================

class ProductionConfig:
    """Production configuration for DataFlow Sales Assistant"""
    
    @staticmethod
    def create_production_dataflow() -> DataFlow:
        """Create production-ready DataFlow configuration"""
        
        # Environment variables for production
        database_url = os.getenv(
            'DATAFLOW_DATABASE_URL',
            'postgresql://sales_app:secure_password@db.production.com:5432/sales_assistant_prod'
        )
        
        redis_url = os.getenv(
            'DATAFLOW_REDIS_URL',
            'redis://redis.production.com:6379/0'
        )
        
        # Production configuration
        config = DataFlowConfig(
            environment=Environment.PRODUCTION,
            
            # Multi-tenancy and security
            multi_tenant=True,
            tenant_isolation_mode="strict",
            enable_row_level_security=True,
            audit_all_operations=True,
            encrypt_sensitive_fields=True,
            
            # Performance settings
            connection_pool_size=50,
            connection_pool_max_overflow=100,
            connection_pool_recycle=3600,
            connection_pool_timeout=30,
            connection_pool_pre_ping=True,
            
            # Caching configuration
            enable_redis_cache=True,
            redis_url=redis_url,
            cache_default_ttl=1800,  # 30 minutes
            cache_max_size_mb=2048,  # 2GB
            
            # Monitoring and logging
            monitoring=True,
            performance_tracking=True,
            slow_query_threshold=2000,  # 2 seconds
            enable_metrics_export=True,
            metrics_export_interval=60,  # 1 minute
            
            # Error handling and resilience
            enable_circuit_breaker=True,
            circuit_breaker_failure_threshold=5,
            circuit_breaker_recovery_timeout=30,
            enable_retry_logic=True,
            max_retry_attempts=3,
            
            # Security settings
            enable_sql_injection_protection=True,
            enable_query_sanitization=True,
            max_query_complexity=1000,
            enable_rate_limiting=True,
            rate_limit_requests_per_minute=1000,
            
            # Backup and recovery
            enable_automatic_backups=True,
            backup_interval_hours=6,
            backup_retention_days=30,
            enable_point_in_time_recovery=True,
            
            # Compliance
            enable_gdpr_compliance=True,
            enable_audit_logging=True,
            audit_log_retention_days=90,
            enable_data_encryption_at_rest=True,
            enable_data_encryption_in_transit=True
        )
        
        # Create DataFlow instance
        db = DataFlow(
            config=config,
            database_url=database_url,
            
            # PostgreSQL production settings
            pool_size=config.connection_pool_size,
            pool_max_overflow=config.connection_pool_max_overflow,
            pool_recycle=config.connection_pool_recycle,
            pool_timeout=config.connection_pool_timeout,
            pool_pre_ping=config.connection_pool_pre_ping,
            
            # Production flags
            echo=False,  # Disable SQL logging in production
            auto_migrate=False,  # Controlled migrations in production
            
            # Security
            enable_rls=True,
            rls_policy_mode="automatic"
        )
        
        return db
    
    @staticmethod
    def create_staging_dataflow() -> DataFlow:
        """Create staging environment DataFlow configuration"""
        
        config = DataFlowConfig(
            environment=Environment.STAGING,
            multi_tenant=True,
            monitoring=True,
            performance_tracking=True,
            
            # Reduced resources for staging
            connection_pool_size=20,
            connection_pool_max_overflow=40,
            
            # Enable more logging for staging
            slow_query_threshold=1000,  # 1 second
            enable_debug_logging=True
        )
        
        db = DataFlow(
            config=config,
            database_url=os.getenv(
                'DATAFLOW_STAGING_DATABASE_URL',
                'postgresql://sales_app:staging_password@db.staging.com:5432/sales_assistant_staging'
            ),
            echo=True,  # Enable SQL logging in staging
            auto_migrate=True  # Allow auto-migration in staging
        )
        
        return db

class SecurityConfiguration:
    """Security configuration and best practices"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def setup_production_security(self) -> Dict[str, Any]:
        """Setup comprehensive production security"""
        
        workflow = WorkflowBuilder()
        
        # 1. Configure row-level security policies
        workflow.add_node("SetupRLSPoliciesNode", "setup_rls", {
            "policies": [
                {
                    "table": "customers",
                    "policy_name": "tenant_isolation_customers",
                    "policy_expression": "tenant_id = current_setting('app.current_tenant_id')::integer"
                },
                {
                    "table": "quotes",
                    "policy_name": "tenant_isolation_quotes",
                    "policy_expression": "tenant_id = current_setting('app.current_tenant_id')::integer"
                },
                {
                    "table": "documents",
                    "policy_name": "tenant_and_security_level",
                    "policy_expression": """
                        tenant_id = current_setting('app.current_tenant_id')::integer
                        AND (
                            security_level = 'public'
                            OR (
                                security_level = 'internal'
                                AND current_setting('app.current_user_role') IN ('admin', 'manager', 'sales_rep')
                            )
                            OR (
                                security_level = 'confidential'
                                AND current_setting('app.current_user_role') IN ('admin', 'manager')
                            )
                            OR (
                                security_level = 'restricted'
                                AND current_setting('app.current_user_role') = 'admin'
                            )
                        )
                    """
                }
            ]
        })
        
        # 2. Setup field-level encryption
        workflow.add_node("SetupFieldEncryptionNode", "setup_encryption", {
            "encrypted_fields": [
                {
                    "table": "customers",
                    "fields": ["tax_id", "custom_fields"],
                    "encryption_key": "customer_data_key"
                },
                {
                    "table": "documents",
                    "fields": ["ai_extracted_data"],
                    "encryption_key": "document_analysis_key"
                },
                {
                    "table": "system_configurations",
                    "fields": ["config_value"],
                    "encryption_condition": "is_sensitive = true",
                    "encryption_key": "system_config_key"
                }
            ]
        })
        
        # 3. Configure audit logging
        workflow.add_node("SetupAuditLoggingNode", "setup_audit", {
            "audit_rules": [
                {
                    "event_type": "data_access",
                    "tables": ["customers", "quotes", "documents"],
                    "operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                    "include_data_changes": True
                },
                {
                    "event_type": "authentication",
                    "operations": ["LOGIN", "LOGOUT", "FAILED_LOGIN"],
                    "include_ip_address": True,
                    "include_user_agent": True
                },
                {
                    "event_type": "authorization",
                    "operations": ["PERMISSION_GRANTED", "PERMISSION_DENIED"],
                    "include_requested_resource": True
                }
            ]
        })
        
        # 4. Setup data masking for non-production environments
        workflow.add_node("SetupDataMaskingNode", "setup_masking", {
            "masking_rules": [
                {
                    "table": "customers",
                    "field": "email",
                    "masking_type": "email",
                    "apply_in_environments": ["development", "staging"]
                },
                {
                    "table": "customers",
                    "field": "phone",
                    "masking_type": "phone",
                    "apply_in_environments": ["development", "staging"]
                },
                {
                    "table": "users",
                    "field": "email",
                    "masking_type": "email",
                    "apply_in_environments": ["development", "staging"]
                }
            ]
        })
        
        # 5. Configure API security
        workflow.add_node("SetupAPISecurityNode", "setup_api_security", {
            "security_measures": [
                {
                    "type": "rate_limiting",
                    "requests_per_minute": 1000,
                    "burst_limit": 100,
                    "per_tenant": True
                },
                {
                    "type": "authentication",
                    "methods": ["jwt", "api_key"],
                    "token_expiry_minutes": 60,
                    "refresh_token_expiry_days": 30
                },
                {
                    "type": "authorization",
                    "rbac_enabled": True,
                    "resource_based_permissions": True
                },
                {
                    "type": "input_validation",
                    "sql_injection_protection": True,
                    "xss_protection": True,
                    "schema_validation": True
                }
            ]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "rls_configured": results.get("setup_rls", {}).get("status") == "success",
            "encryption_configured": results.get("setup_encryption", {}).get("status") == "success",
            "audit_logging_configured": results.get("setup_audit", {}).get("status") == "success",
            "data_masking_configured": results.get("setup_masking", {}).get("status") == "success",
            "api_security_configured": results.get("setup_api_security", {}).get("status") == "success",
            "security_setup_completed_at": datetime.now().isoformat()
        }
    
    def run_security_assessment(self) -> Dict[str, Any]:
        """Run comprehensive security assessment"""
        
        workflow = WorkflowBuilder()
        
        # 1. Check RLS policy compliance
        workflow.add_node("AssessRLSComplianceNode", "assess_rls", {
            "check_all_tenant_tables": True,
            "verify_policy_effectiveness": True
        })
        
        # 2. Verify encryption status
        workflow.add_node("AssessEncryptionStatusNode", "assess_encryption", {
            "check_field_level_encryption": True,
            "check_data_at_rest_encryption": True,
            "check_data_in_transit_encryption": True
        })
        
        # 3. Audit log integrity check
        workflow.add_node("AssessAuditIntegrityNode", "assess_audit", {
            "check_audit_completeness": True,
            "verify_audit_tamper_protection": True,
            "check_retention_compliance": True
        })
        
        # 4. Access control verification
        workflow.add_node("AssessAccessControlNode", "assess_access", {
            "check_user_permissions": True,
            "verify_role_assignments": True,
            "check_privilege_escalation": True
        })
        
        # 5. Security vulnerability scan
        workflow.add_node("SecurityVulnerabilityScanNode", "vulnerability_scan", {
            "scan_sql_injection": True,
            "scan_privilege_escalation": True,
            "scan_data_exposure": True,
            "scan_authentication_bypass": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "assessment_timestamp": datetime.now().isoformat(),
            "rls_compliance": results.get("assess_rls", {}).get("result", {}),
            "encryption_status": results.get("assess_encryption", {}).get("result", {}),
            "audit_integrity": results.get("assess_audit", {}).get("result", {}),
            "access_control": results.get("assess_access", {}).get("result", {}),
            "vulnerabilities": results.get("vulnerability_scan", {}).get("result", []),
            "overall_security_score": self._calculate_security_score(results)
        }
    
    def _calculate_security_score(self, assessment_results: Dict) -> float:
        """Calculate overall security score based on assessment results"""
        
        # Simplified scoring algorithm
        scores = []
        
        # RLS compliance score
        rls_result = assessment_results.get("assess_rls", {}).get("result", {})
        rls_score = rls_result.get("compliance_percentage", 0) / 100
        scores.append(rls_score * 0.25)  # 25% weight
        
        # Encryption score
        encryption_result = assessment_results.get("assess_encryption", {}).get("result", {})
        encryption_score = encryption_result.get("encryption_coverage", 0) / 100
        scores.append(encryption_score * 0.25)  # 25% weight
        
        # Audit integrity score
        audit_result = assessment_results.get("assess_audit", {}).get("result", {})
        audit_score = audit_result.get("integrity_score", 0) / 100
        scores.append(audit_score * 0.20)  # 20% weight
        
        # Access control score
        access_result = assessment_results.get("assess_access", {}).get("result", {})
        access_score = access_result.get("compliance_score", 0) / 100
        scores.append(access_score * 0.20)  # 20% weight
        
        # Vulnerability score (inverted - fewer vulnerabilities = higher score)
        vuln_result = assessment_results.get("vulnerability_scan", {}).get("result", [])
        critical_vulns = len([v for v in vuln_result if v.get("severity") == "critical"])
        vuln_score = max(0, 1 - (critical_vulns * 0.2))  # Each critical vuln reduces score by 20%
        scores.append(vuln_score * 0.10)  # 10% weight
        
        return sum(scores)

class MonitoringConfiguration:
    """Monitoring and alerting configuration"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def setup_production_monitoring(self) -> Dict[str, Any]:
        """Setup comprehensive production monitoring"""
        
        workflow = WorkflowBuilder()
        
        # 1. Database monitoring
        workflow.add_node("SetupDatabaseMonitoringNode", "db_monitoring", {
            "metrics": [
                {
                    "name": "connection_pool_utilization",
                    "query": "SELECT * FROM pg_stat_activity",
                    "threshold_warning": 0.7,
                    "threshold_critical": 0.9,
                    "collection_interval_seconds": 30
                },
                {
                    "name": "slow_query_count",
                    "query": "SELECT count(*) FROM pg_stat_statements WHERE mean_time > 2000",
                    "threshold_warning": 10,
                    "threshold_critical": 50,
                    "collection_interval_seconds": 60
                },
                {
                    "name": "database_size",
                    "query": "SELECT pg_database_size(current_database())",
                    "threshold_warning": 50 * 1024 * 1024 * 1024,  # 50GB
                    "threshold_critical": 80 * 1024 * 1024 * 1024,  # 80GB
                    "collection_interval_seconds": 300
                },
                {
                    "name": "deadlock_count",
                    "query": "SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()",
                    "threshold_warning": 1,
                    "threshold_critical": 5,
                    "collection_interval_seconds": 60
                }
            ]
        })
        
        # 2. Application performance monitoring
        workflow.add_node("SetupApplicationMonitoringNode", "app_monitoring", {
            "metrics": [
                {
                    "name": "workflow_execution_time",
                    "collection_method": "histogram",
                    "threshold_warning": 5000,  # 5 seconds
                    "threshold_critical": 15000,  # 15 seconds
                    "collection_interval_seconds": 10
                },
                {
                    "name": "cache_hit_rate",
                    "collection_method": "gauge",
                    "threshold_warning": 0.7,
                    "threshold_critical": 0.5,
                    "collection_interval_seconds": 60
                },
                {
                    "name": "error_rate",
                    "collection_method": "counter",
                    "threshold_warning": 0.01,  # 1%
                    "threshold_critical": 0.05,  # 5%
                    "collection_interval_seconds": 30
                },
                {
                    "name": "memory_usage",
                    "collection_method": "gauge",
                    "threshold_warning": 0.8,  # 80%
                    "threshold_critical": 0.95,  # 95%
                    "collection_interval_seconds": 30
                }
            ]
        })
        
        # 3. Business metrics monitoring
        workflow.add_node("SetupBusinessMonitoringNode", "business_monitoring", {
            "metrics": [
                {
                    "name": "quotes_created_per_hour",
                    "collection_method": "counter",
                    "threshold_warning": 100,
                    "collection_interval_seconds": 300
                },
                {
                    "name": "document_processing_success_rate",
                    "collection_method": "gauge",
                    "threshold_warning": 0.9,
                    "threshold_critical": 0.8,
                    "collection_interval_seconds": 300
                },
                {
                    "name": "user_session_duration",
                    "collection_method": "histogram",
                    "collection_interval_seconds": 300
                },
                {
                    "name": "api_requests_per_minute",
                    "collection_method": "counter",
                    "threshold_warning": 10000,
                    "threshold_critical": 15000,
                    "collection_interval_seconds": 60
                }
            ]
        })
        
        # 4. Setup alerting channels
        workflow.add_node("SetupAlertingChannelsNode", "alerting_channels", {
            "channels": [
                {
                    "name": "email_alerts",
                    "type": "email",
                    "configuration": {
                        "smtp_server": os.getenv("SMTP_SERVER", "smtp.production.com"),
                        "recipients": [
                            "ops-team@company.com",
                            "dev-team@company.com"
                        ],
                        "severity_filters": ["warning", "critical"]
                    }
                },
                {
                    "name": "slack_alerts",
                    "type": "webhook",
                    "configuration": {
                        "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
                        "channel": "#alerts",
                        "severity_filters": ["critical"]
                    }
                },
                {
                    "name": "pagerduty_alerts",
                    "type": "pagerduty",
                    "configuration": {
                        "integration_key": os.getenv("PAGERDUTY_INTEGRATION_KEY"),
                        "severity_filters": ["critical"]
                    }
                },
                {
                    "name": "dashboard_alerts",
                    "type": "dashboard",
                    "configuration": {
                        "dashboard_url": "/monitoring/alerts",
                        "severity_filters": ["info", "warning", "critical"]
                    }
                }
            ]
        })
        
        # 5. Setup alert rules
        workflow.add_node("SetupAlertRulesNode", "alert_rules", {
            "rules": [
                {
                    "name": "high_database_connections",
                    "condition": "connection_pool_utilization > 0.8",
                    "severity": "warning",
                    "notification_channels": ["email_alerts", "dashboard_alerts"],
                    "cooldown_minutes": 5
                },
                {
                    "name": "critical_database_connections",
                    "condition": "connection_pool_utilization > 0.95",
                    "severity": "critical",
                    "notification_channels": ["email_alerts", "slack_alerts", "pagerduty_alerts"],
                    "cooldown_minutes": 1
                },
                {
                    "name": "slow_queries_detected",
                    "condition": "slow_query_count > 10",
                    "severity": "warning",
                    "notification_channels": ["email_alerts", "dashboard_alerts"],
                    "cooldown_minutes": 10
                },
                {
                    "name": "high_error_rate",
                    "condition": "error_rate > 0.05",
                    "severity": "critical",
                    "notification_channels": ["email_alerts", "slack_alerts", "pagerduty_alerts"],
                    "cooldown_minutes": 2
                },
                {
                    "name": "low_cache_hit_rate",
                    "condition": "cache_hit_rate < 0.5",
                    "severity": "warning",
                    "notification_channels": ["email_alerts", "dashboard_alerts"],
                    "cooldown_minutes": 15
                }
            ]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "db_monitoring_configured": results.get("db_monitoring", {}).get("status") == "success",
            "app_monitoring_configured": results.get("app_monitoring", {}).get("status") == "success",
            "business_monitoring_configured": results.get("business_monitoring", {}).get("status") == "success",
            "alerting_channels_configured": results.get("alerting_channels", {}).get("status") == "success",
            "alert_rules_configured": results.get("alert_rules", {}).get("status") == "success",
            "monitoring_setup_completed_at": datetime.now().isoformat()
        }

class BackupAndRecoveryConfiguration:
    """Backup and disaster recovery configuration"""
    
    def __init__(self, db: DataFlow):
        self.db = db
        self.runtime = LocalRuntime()
    
    def setup_backup_strategy(self) -> Dict[str, Any]:
        """Setup comprehensive backup and recovery strategy"""
        
        workflow = WorkflowBuilder()
        
        # 1. Configure automatic backups
        workflow.add_node("SetupAutomaticBackupsNode", "automatic_backups", {
            "backup_schedules": [
                {
                    "name": "full_daily_backup",
                    "type": "full",
                    "schedule": "0 2 * * *",  # 2 AM daily
                    "retention_days": 30,
                    "compression": True,
                    "encryption": True,
                    "storage_location": "s3://backups.company.com/dataflow/full/"
                },
                {
                    "name": "incremental_hourly_backup",
                    "type": "incremental",
                    "schedule": "0 * * * *",  # Every hour
                    "retention_days": 7,
                    "compression": True,
                    "encryption": True,
                    "storage_location": "s3://backups.company.com/dataflow/incremental/"
                },
                {
                    "name": "transaction_log_backup",
                    "type": "transaction_log",
                    "schedule": "*/15 * * * *",  # Every 15 minutes
                    "retention_days": 3,
                    "compression": False,
                    "encryption": True,
                    "storage_location": "s3://backups.company.com/dataflow/logs/"
                }
            ]
        })
        
        # 2. Configure point-in-time recovery
        workflow.add_node("SetupPITRNode", "pitr_setup", {
            "enable_continuous_archiving": True,
            "archive_timeout_minutes": 15,
            "archive_location": "s3://backups.company.com/dataflow/wal/",
            "max_wal_size_gb": 10,
            "checkpoint_completion_target": 0.7
        })
        
        # 3. Setup cross-region replication
        workflow.add_node("SetupReplicationNode", "replication_setup", {
            "replicas": [
                {
                    "name": "disaster_recovery_replica",
                    "location": "us-west-2",
                    "type": "asynchronous",
                    "lag_threshold_seconds": 60,
                    "purpose": "disaster_recovery"
                },
                {
                    "name": "read_replica_analytics",
                    "location": "us-east-1",
                    "type": "asynchronous",
                    "lag_threshold_seconds": 300,
                    "purpose": "analytics_workload"
                }
            ]
        })
        
        # 4. Configure backup monitoring
        workflow.add_node("SetupBackupMonitoringNode", "backup_monitoring", {
            "monitoring_checks": [
                {
                    "name": "backup_completion_check",
                    "schedule": "0 3 * * *",  # 3 AM daily (after backup)
                    "check_last_24_hours": True,
                    "alert_on_failure": True
                },
                {
                    "name": "backup_integrity_check",
                    "schedule": "0 4 * * 0",  # 4 AM every Sunday
                    "perform_restore_test": True,
                    "test_database": "backup_test_db",
                    "alert_on_failure": True
                },
                {
                    "name": "replication_lag_check",
                    "schedule": "*/10 * * * *",  # Every 10 minutes
                    "max_acceptable_lag_seconds": 300,
                    "alert_on_threshold": True
                }
            ]
        })
        
        # 5. Create disaster recovery procedures
        workflow.add_node("SetupDRProceduresNode", "dr_procedures", {
            "procedures": [
                {
                    "name": "complete_system_failure",
                    "steps": [
                        "assess_failure_scope",
                        "activate_disaster_recovery_site",
                        "restore_from_latest_backup",
                        "redirect_application_traffic",
                        "verify_system_functionality",
                        "communicate_status_to_stakeholders"
                    ],
                    "estimated_rto_minutes": 60,  # Recovery Time Objective
                    "estimated_rpo_minutes": 15   # Recovery Point Objective
                },
                {
                    "name": "database_corruption",
                    "steps": [
                        "stop_application_writes",
                        "assess_corruption_extent",
                        "restore_from_point_in_time",
                        "verify_data_integrity",
                        "resume_application_operations"
                    ],
                    "estimated_rto_minutes": 30,
                    "estimated_rpo_minutes": 15
                },
                {
                    "name": "accidental_data_deletion",
                    "steps": [
                        "identify_affected_data",
                        "calculate_recovery_point",
                        "restore_specific_tables_or_records",
                        "verify_restored_data",
                        "audit_deletion_cause"
                    ],
                    "estimated_rto_minutes": 45,
                    "estimated_rpo_minutes": 15
                }
            ]
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "automatic_backups_configured": results.get("automatic_backups", {}).get("status") == "success",
            "pitr_configured": results.get("pitr_setup", {}).get("status") == "success",
            "replication_configured": results.get("replication_setup", {}).get("status") == "success",
            "backup_monitoring_configured": results.get("backup_monitoring", {}).get("status") == "success",
            "dr_procedures_documented": results.get("dr_procedures", {}).get("status") == "success",
            "backup_strategy_completed_at": datetime.now().isoformat()
        }
    
    def test_disaster_recovery(self, scenario: str = "complete_system_failure") -> Dict[str, Any]:
        """Test disaster recovery procedures"""
        
        workflow = WorkflowBuilder()
        
        # 1. Initialize DR test
        workflow.add_node("InitializeDRTestNode", "init_dr_test", {
            "scenario": scenario,
            "test_environment": "dr_test",
            "test_started_at": datetime.now(),
            "notify_stakeholders": True
        })
        
        # 2. Execute DR scenario
        if scenario == "complete_system_failure":
            workflow.add_node("SimulateSystemFailureNode", "simulate_failure", {
                "failure_type": "complete_outage",
                "affected_components": ["database", "application", "cache"]
            })
            
            workflow.add_node("ActivateDRSiteNode", "activate_dr", {
                "dr_site_location": "us-west-2",
                "activate_all_services": True
            })
            
            workflow.add_node("RestoreFromBackupNode", "restore_backup", {
                "backup_type": "latest_full_with_incremental",
                "target_database": "dr_test_db",
                "verify_integrity": True
            })
        
        elif scenario == "database_corruption":
            workflow.add_node("SimulateDataCorruptionNode", "simulate_corruption", {
                "corruption_type": "partial_table_corruption",
                "affected_tables": ["quotes", "quote_line_items"]
            })
            
            workflow.add_node("RestorePointInTimeNode", "pitr_restore", {
                "recovery_target_time": datetime.now() - timedelta(hours=1),
                "target_database": "dr_test_db"
            })
        
        # 3. Verify recovery
        workflow.add_node("VerifyRecoveryNode", "verify_recovery", {
            "verification_tests": [
                "database_connectivity",
                "data_integrity_check",
                "application_functionality",
                "performance_baseline"
            ]
        })
        
        # 4. Measure RTO/RPO
        workflow.add_node("MeasureRTORPONode", "measure_rto_rpo", {
            "calculate_recovery_time": True,
            "calculate_data_loss": True,
            "compare_to_objectives": True
        })
        
        # 5. Generate DR test report
        workflow.add_node("GenerateDRReportNode", "generate_report", {
            "include_timeline": True,
            "include_issues_encountered": True,
            "include_recommendations": True,
            "distribute_to_stakeholders": True
        })
        
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "test_scenario": scenario,
            "test_id": results.get("init_dr_test", {}).get("test_id"),
            "recovery_successful": results.get("verify_recovery", {}).get("status") == "success",
            "actual_rto_minutes": results.get("measure_rto_rpo", {}).get("actual_rto_minutes"),
            "actual_rpo_minutes": results.get("measure_rto_rpo", {}).get("actual_rpo_minutes"),
            "meets_objectives": results.get("measure_rto_rpo", {}).get("meets_objectives"),
            "test_report_generated": results.get("generate_report", {}).get("status") == "success",
            "test_completed_at": datetime.now().isoformat()
        }

# ==============================================================================
# PRODUCTION BEST PRACTICES GUIDE
# ==============================================================================

class ProductionBestPractices:
    """Production deployment best practices and guidelines"""
    
    @staticmethod
    def get_deployment_checklist() -> Dict[str, List[str]]:
        """Get comprehensive production deployment checklist"""
        
        return {
            "pre_deployment": [
                "✓ All tests passing in staging environment",
                "✓ Database migration scripts reviewed and tested",
                "✓ Security audit completed and issues resolved",
                "✓ Performance testing completed with acceptable results",
                "✓ Backup and recovery procedures tested",
                "✓ Monitoring and alerting configured",
                "✓ Documentation updated",
                "✓ Rollback plan prepared and tested",
                "✓ Stakeholder notification sent",
                "✓ Maintenance window scheduled"
            ],
            "deployment": [
                "✓ Create pre-deployment backup",
                "✓ Deploy to production during maintenance window",
                "✓ Run database migrations with verification",
                "✓ Deploy application code with blue-green strategy",
                "✓ Verify all services are running",
                "✓ Run smoke tests on critical functionality",
                "✓ Monitor system metrics for anomalies",
                "✓ Verify data integrity",
                "✓ Test user authentication and authorization",
                "✓ Confirm external integrations are working"
            ],
            "post_deployment": [
                "✓ Monitor system performance for 2+ hours",
                "✓ Verify all alerts are functioning",
                "✓ Check log files for errors or warnings",
                "✓ Validate business metrics are being collected",
                "✓ Test critical user workflows",
                "✓ Confirm backup jobs are running successfully",
                "✓ Update runbooks and documentation",
                "✓ Send deployment completion notification",
                "✓ Schedule post-deployment review meeting",
                "✓ Archive deployment artifacts"
            ]
        }
    
    @staticmethod
    def get_performance_tuning_guide() -> Dict[str, Any]:
        """Get performance tuning recommendations"""
        
        return {
            "database_optimization": {
                "connection_pooling": {
                    "recommendation": "Configure connection pooling based on workload",
                    "settings": {
                        "pool_size": "20-50 for typical workloads",
                        "max_overflow": "2x pool_size",
                        "pool_recycle": "3600 seconds (1 hour)",
                        "pool_pre_ping": "True for reliability"
                    }
                },
                "indexing": {
                    "recommendation": "Create indexes for common query patterns",
                    "guidelines": [
                        "Index tenant_id for all multi-tenant tables",
                        "Composite indexes for frequently filtered columns",
                        "Partial indexes for filtered queries",
                        "GIN indexes for full-text search",
                        "Monitor index usage and remove unused indexes"
                    ]
                },
                "query_optimization": {
                    "recommendation": "Optimize slow queries",
                    "techniques": [
                        "Use EXPLAIN ANALYZE to understand query plans",
                        "Avoid N+1 query patterns",
                        "Use bulk operations for multiple records",
                        "Implement query result caching",
                        "Consider read replicas for analytics workloads"
                    ]
                }
            },
            "application_optimization": {
                "caching": {
                    "recommendation": "Implement multi-level caching",
                    "strategies": [
                        "L1: In-memory application cache (5-15 minutes TTL)",
                        "L2: Redis distributed cache (30-60 minutes TTL)",
                        "L3: Database query result cache (1-4 hours TTL)",
                        "Implement cache warming for critical data",
                        "Use cache invalidation on data changes"
                    ]
                },
                "bulk_operations": {
                    "recommendation": "Use bulk operations for high-volume processing",
                    "best_practices": [
                        "Batch size: 500-2000 records per batch",
                        "Use COPY mode for fastest inserts",
                        "Disable triggers during bulk operations",
                        "Process in transactions with rollback capability",
                        "Monitor memory usage during bulk operations"
                    ]
                }
            },
            "monitoring_optimization": {
                "metrics_collection": {
                    "recommendation": "Collect key performance indicators",
                    "important_metrics": [
                        "Response time percentiles (50th, 95th, 99th)",
                        "Request throughput (requests per second)",
                        "Error rates by operation type",
                        "Database connection pool utilization",
                        "Cache hit rates by cache level",
                        "Memory and CPU utilization"
                    ]
                }
            }
        }
    
    @staticmethod
    def get_security_hardening_guide() -> Dict[str, Any]:
        """Get security hardening recommendations"""
        
        return {
            "database_security": {
                "access_control": [
                    "Enable row-level security (RLS) for all tenant-aware tables",
                    "Use least-privilege principle for database users",
                    "Implement role-based access control (RBAC)",
                    "Regular audit of user permissions and access patterns",
                    "Use strong, unique passwords with regular rotation"
                ],
                "encryption": [
                    "Enable encryption at rest for sensitive data",
                    "Use TLS 1.3 for all database connections",
                    "Implement field-level encryption for PII data",
                    "Encrypt database backups",
                    "Use encrypted storage for logs and temporary files"
                ]
            },
            "application_security": [
                "Implement input validation and sanitization",
                "Use parameterized queries to prevent SQL injection",
                "Enable CSRF protection",
                "Implement rate limiting to prevent abuse",
                "Use secure session management",
                "Regular security vulnerability scanning",
                "Keep all dependencies updated",
                "Implement Content Security Policy (CSP)"
            ],
            "infrastructure_security": [
                "Use firewalls to restrict network access",
                "Implement VPN access for administrative tasks",
                "Regular OS and system updates",
                "Use intrusion detection systems",
                "Implement log monitoring and anomaly detection",
                "Regular security assessments and penetration testing",
                "Use secrets management for API keys and passwords",
                "Implement network segmentation"
            ]
        }

# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

def demo_production_setup():
    """Demonstrate production configuration setup"""
    
    print("=== DataFlow Production Configuration Demo ===")
    
    # 1. Create production DataFlow instance
    print("\n--- Creating Production DataFlow ---")
    production_db = ProductionConfig.create_production_dataflow()
    print("Production DataFlow instance created with comprehensive configuration")
    
    # 2. Setup security
    print("\n--- Configuring Security ---")
    security_config = SecurityConfiguration(production_db)
    security_setup = security_config.setup_production_security()
    print(f"Security configuration completed: {all(security_setup.values())}")
    
    # 3. Setup monitoring
    print("\n--- Configuring Monitoring ---")
    monitoring_config = MonitoringConfiguration(production_db)
    monitoring_setup = monitoring_config.setup_production_monitoring()
    print(f"Monitoring configuration completed: {all(monitoring_setup.values())}")
    
    # 4. Setup backup and recovery
    print("\n--- Configuring Backup & Recovery ---")
    backup_config = BackupAndRecoveryConfiguration(production_db)
    backup_setup = backup_config.setup_backup_strategy()
    print(f"Backup strategy configured: {all(backup_setup.values())}")
    
    # 5. Display deployment checklist
    print("\n--- Production Deployment Checklist ---")
    checklist = ProductionBestPractices.get_deployment_checklist()
    
    for phase, items in checklist.items():
        print(f"\n{phase.upper().replace('_', ' ')}:")
        for item in items[:3]:  # Show first 3 items
            print(f"  {item}")
        print(f"  ... and {len(items)-3} more items")
    
    # 6. Security assessment
    print("\n--- Running Security Assessment ---")
    security_assessment = security_config.run_security_assessment()
    print(f"Security score: {security_assessment['overall_security_score']:.2%}")
    
    # 7. Test disaster recovery
    print("\n--- Testing Disaster Recovery ---")
    dr_test = backup_config.test_disaster_recovery("database_corruption")
    print(f"DR test completed: {dr_test['recovery_successful']}")
    print(f"Recovery time: {dr_test.get('actual_rto_minutes', 'N/A')} minutes")
    
    print("\n=== Production Configuration Complete ===")
    print("\nNext steps:")
    print("1. Review and customize configuration for your environment")
    print("2. Run full test suite in staging environment")
    print("3. Schedule deployment window")
    print("4. Execute deployment following the checklist")
    print("5. Monitor system performance post-deployment")

if __name__ == "__main__":
    demo_production_setup()