"""
Data Quality Monitoring and Validation System
Comprehensive monitoring and validation for supplier/brand intelligence data
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from src.models.production_models import db

logger = logging.getLogger(__name__)

class DataQualityLevel(Enum):
    """Data quality assessment levels"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 75-89%
    FAIR = "fair"           # 60-74%
    POOR = "poor"           # 40-59%
    CRITICAL = "critical"    # 0-39%

class ValidationStatus(Enum):
    """Validation status types"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"
    SKIPPED = "skipped"

@dataclass
class DataQualityMetric:
    """Data quality metric definition"""
    name: str
    description: str
    weight: float  # 0.0 to 1.0
    threshold_excellent: float
    threshold_good: float
    threshold_fair: float
    threshold_poor: float

@dataclass
class ValidationRule:
    """Data validation rule definition"""
    name: str
    description: str
    rule_type: str  # completeness, consistency, accuracy, timeliness, validity
    severity: str   # critical, high, medium, low
    validation_logic: str
    remediation_suggestion: str

@dataclass
class QualityAssessmentResult:
    """Quality assessment result"""
    entity_type: str
    entity_id: int
    overall_score: float
    quality_level: DataQualityLevel
    metric_scores: Dict[str, float]
    validation_results: List[Dict[str, Any]]
    recommendations: List[str]
    assessed_at: datetime

class DataQualityMonitoringSystem:
    """Comprehensive data quality monitoring and validation system"""
    
    def __init__(self):
        self.runtime = LocalRuntime()
        self.quality_metrics = self._initialize_quality_metrics()
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_quality_metrics(self) -> Dict[str, DataQualityMetric]:
        """Initialize data quality metrics"""
        return {
            "completeness": DataQualityMetric(
                name="Data Completeness",
                description="Percentage of required fields populated",
                weight=0.25,
                threshold_excellent=95.0,
                threshold_good=85.0,
                threshold_fair=70.0,
                threshold_poor=50.0
            ),
            "consistency": DataQualityMetric(
                name="Data Consistency",
                description="Consistency across related data points",
                weight=0.20,
                threshold_excellent=95.0,
                threshold_good=85.0,
                threshold_fair=75.0,
                threshold_poor=60.0
            ),
            "accuracy": DataQualityMetric(
                name="Data Accuracy",
                description="Accuracy validated against external sources",
                weight=0.25,
                threshold_excellent=90.0,
                threshold_good=80.0,
                threshold_fair=70.0,
                threshold_poor=55.0
            ),
            "timeliness": DataQualityMetric(
                name="Data Timeliness",
                description="Freshness and currency of data",
                weight=0.15,
                threshold_excellent=90.0,
                threshold_good=75.0,
                threshold_fair=60.0,
                threshold_poor=40.0
            ),
            "validity": DataQualityMetric(
                name="Data Validity",
                description="Adherence to data format and business rules",
                weight=0.15,
                threshold_excellent=98.0,
                threshold_good=92.0,
                threshold_fair=85.0,
                threshold_poor=70.0
            )
        }
    
    def _initialize_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """Initialize validation rules by entity type"""
        return {
            "supplier_profile": [
                ValidationRule(
                    name="Required Fields Check",
                    description="Verify all required fields are populated",
                    rule_type="completeness",
                    severity="critical",
                    validation_logic="check_required_fields(['supplier_id', 'company_size', 'primary_industries'])",
                    remediation_suggestion="Populate missing required fields through data collection workflows"
                ),
                ValidationRule(
                    name="Business Logic Consistency",
                    description="Verify business logic consistency (e.g., employee count vs company size)",
                    rule_type="consistency",
                    severity="high",
                    validation_logic="validate_employee_count_vs_company_size()",
                    remediation_suggestion="Review and correct inconsistent data points"
                ),
                ValidationRule(
                    name="Financial Data Accuracy",
                    description="Validate financial ratings and scores against external sources",
                    rule_type="accuracy",
                    severity="high",
                    validation_logic="cross_validate_financial_data()",
                    remediation_suggestion="Re-verify financial data with authoritative sources"
                ),
                ValidationRule(
                    name="Geographic Data Validity",
                    description="Validate geographic coverage and locations",
                    rule_type="validity",
                    severity="medium",
                    validation_logic="validate_geographic_data()",
                    remediation_suggestion="Correct invalid geographic references"
                ),
                ValidationRule(
                    name="Data Freshness Check",
                    description="Ensure data is updated within acceptable timeframes",
                    rule_type="timeliness",
                    severity="medium",
                    validation_logic="check_data_freshness(max_age_days=90)",
                    remediation_suggestion="Refresh outdated data through enrichment workflows"
                )
            ],
            "brand_intelligence": [
                ValidationRule(
                    name="Market Position Consistency",
                    description="Verify market position aligns with pricing strategy and quality ratings",
                    rule_type="consistency",
                    severity="high",
                    validation_logic="validate_market_position_alignment()",
                    remediation_suggestion="Review and align market position with supporting data"
                ),
                ValidationRule(
                    name="Rating Validity Range",
                    description="Ensure all ratings are within valid ranges (1-10 scale)",
                    rule_type="validity",
                    severity="critical",
                    validation_logic="validate_rating_ranges()",
                    remediation_suggestion="Correct out-of-range rating values"
                ),
                ValidationRule(
                    name="Competitive Data Accuracy",
                    description="Validate competitive intelligence against market research",
                    rule_type="accuracy",
                    severity="medium",
                    validation_logic="cross_validate_competitive_data()",
                    remediation_suggestion="Update competitive intelligence from reliable sources"
                )
            ],
            "product_intelligence": [
                ValidationRule(
                    name="Technical Specifications Completeness",
                    description="Verify comprehensive technical specifications are present",
                    rule_type="completeness",
                    severity="high",
                    validation_logic="check_technical_specs_completeness()",
                    remediation_suggestion="Collect missing technical specifications"
                ),
                ValidationRule(
                    name="Use Case Scenario Validity",
                    description="Validate use case scenarios are realistic and detailed",
                    rule_type="validity",
                    severity="medium",
                    validation_logic="validate_use_case_scenarios()",
                    remediation_suggestion="Review and enhance use case scenario details"
                ),
                ValidationRule(
                    name="Safety Compliance Accuracy",
                    description="Verify safety ratings and compliance data accuracy",
                    rule_type="accuracy",
                    severity="critical",
                    validation_logic="validate_safety_compliance()",
                    remediation_suggestion="Re-verify safety compliance with authoritative sources"
                ),
                ValidationRule(
                    name="Compatibility Matrix Consistency",
                    description="Ensure compatibility data is consistent and logical",
                    rule_type="consistency",
                    severity="medium",
                    validation_logic="validate_compatibility_matrix()",
                    remediation_suggestion="Review and correct compatibility inconsistencies"
                )
            ],
            "market_intelligence": [
                ValidationRule(
                    name="Pricing Data Freshness",
                    description="Ensure pricing data is current and frequently updated",
                    rule_type="timeliness",
                    severity="critical",
                    validation_logic="check_pricing_data_freshness(max_age_hours=24)",
                    remediation_suggestion="Implement real-time pricing data collection"
                ),
                ValidationRule(
                    name="Market Trend Consistency",
                    description="Verify market trends align with supporting data",
                    rule_type="consistency",
                    severity="high",
                    validation_logic="validate_market_trend_alignment()",
                    remediation_suggestion="Review trend indicators and supporting data"
                ),
                ValidationRule(
                    name="Availability Status Accuracy",
                    description="Validate availability status against supplier data",
                    rule_type="accuracy",
                    severity="high",
                    validation_logic="cross_validate_availability_status()",
                    remediation_suggestion="Sync availability data with supplier systems"
                )
            ]
        }
    
    def assess_data_quality(self, entity_type: str, entity_id: int) -> QualityAssessmentResult:
        """
        Comprehensive data quality assessment for an entity
        
        Args:
            entity_type: Type of entity (supplier_profile, brand_intelligence, etc.)
            entity_id: Entity ID to assess
            
        Returns:
            Quality assessment result with scores and recommendations
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Get entity data
        if entity_type == "supplier_profile":
            workflow.add_node("SupplierProfileReadNode", "get_entity", {"id": entity_id})
        elif entity_type == "brand_intelligence":
            workflow.add_node("BrandIntelligenceReadNode", "get_entity", {"id": entity_id})
        elif entity_type == "product_intelligence":
            workflow.add_node("ProductIntelligenceReadNode", "get_entity", {"id": entity_id})
        elif entity_type == "market_intelligence":
            workflow.add_node("MarketIntelligenceReadNode", "get_entity", {"id": entity_id})
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Step 2: Assess completeness
        workflow.add_node("CompletenessAssessmentNode", "assess_completeness", {
            "entity_type": entity_type,
            "assessment_criteria": self._get_completeness_criteria(entity_type)
        })
        workflow.add_connection("get_entity", "entity_data", "assess_completeness", "data")
        
        # Step 3: Assess consistency
        workflow.add_node("ConsistencyAssessmentNode", "assess_consistency", {
            "entity_type": entity_type,
            "consistency_rules": self._get_consistency_rules(entity_type)
        })
        workflow.add_connection("get_entity", "entity_data", "assess_consistency", "data")
        
        # Step 4: Assess accuracy
        workflow.add_node("AccuracyAssessmentNode", "assess_accuracy", {
            "entity_type": entity_type,
            "validation_sources": self._get_validation_sources(entity_type)
        })
        workflow.add_connection("get_entity", "entity_data", "assess_accuracy", "data")
        
        # Step 5: Assess timeliness
        workflow.add_node("TimelinessAssessmentNode", "assess_timeliness", {
            "entity_type": entity_type,
            "freshness_requirements": self._get_freshness_requirements(entity_type)
        })
        workflow.add_connection("get_entity", "entity_data", "assess_timeliness", "data")
        
        # Step 6: Assess validity
        workflow.add_node("ValidityAssessmentNode", "assess_validity", {
            "entity_type": entity_type,
            "validation_rules": self.validation_rules.get(entity_type, [])
        })
        workflow.add_connection("get_entity", "entity_data", "assess_validity", "data")
        
        # Step 7: Calculate overall quality score
        workflow.add_node("QualityScoreCalculationNode", "calculate_score", {
            "metrics": self.quality_metrics,
            "weighting_strategy": "weighted_average"
        })
        workflow.add_connection("assess_completeness", "score", "calculate_score", "completeness_score")
        workflow.add_connection("assess_consistency", "score", "calculate_score", "consistency_score")
        workflow.add_connection("assess_accuracy", "score", "calculate_score", "accuracy_score")
        workflow.add_connection("assess_timeliness", "score", "calculate_score", "timeliness_score")
        workflow.add_connection("assess_validity", "score", "calculate_score", "validity_score")
        
        # Step 8: Generate recommendations
        workflow.add_node("QualityRecommendationNode", "generate_recommendations", {
            "entity_type": entity_type,
            "recommendation_categories": [
                "data_collection", "data_cleansing", "validation",
                "enrichment", "monitoring"
            ]
        })
        workflow.add_connection("calculate_score", "detailed_scores", "generate_recommendations", "quality_scores")
        workflow.add_connection("assess_validity", "validation_results", "generate_recommendations", "validation_issues")
        
        # Execute workflow
        try:
            results, run_id = self.runtime.execute(workflow.build())
            
            # Extract results
            overall_score = results.get("calculate_score", {}).get("overall_score", 0.0)
            metric_scores = results.get("calculate_score", {}).get("metric_scores", {})
            validation_results = results.get("assess_validity", {}).get("validation_results", [])
            recommendations = results.get("generate_recommendations", {}).get("recommendations", [])
            
            # Determine quality level
            quality_level = self._determine_quality_level(overall_score)
            
            return QualityAssessmentResult(
                entity_type=entity_type,
                entity_id=entity_id,
                overall_score=overall_score,
                quality_level=quality_level,
                metric_scores=metric_scores,
                validation_results=validation_results,
                recommendations=recommendations,
                assessed_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Quality assessment failed for {entity_type} {entity_id}: {str(e)}")
            raise
    
    def bulk_quality_assessment(
        self, 
        entity_type: str, 
        entity_ids: List[int],
        parallel_processing: bool = True
    ) -> Dict[int, QualityAssessmentResult]:
        """
        Bulk data quality assessment for multiple entities
        
        Args:
            entity_type: Type of entities to assess
            entity_ids: List of entity IDs
            parallel_processing: Whether to process in parallel
            
        Returns:
            Dictionary mapping entity_id to quality assessment result
        """
        results = {}
        
        if parallel_processing:
            # Create bulk assessment workflow
            workflow = WorkflowBuilder()
            
            # Add bulk assessment node
            workflow.add_node("BulkQualityAssessmentNode", "bulk_assess", {
                "entity_type": entity_type,
                "entity_ids": entity_ids,
                "batch_size": 20,
                "quality_metrics": self.quality_metrics,
                "validation_rules": self.validation_rules.get(entity_type, [])
            })
            
            # Execute workflow
            workflow_results, _ = self.runtime.execute(workflow.build())
            
            # Convert results to assessment objects
            for entity_id, assessment_data in workflow_results.get("bulk_assess", {}).items():
                results[entity_id] = QualityAssessmentResult(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    overall_score=assessment_data.get("overall_score", 0.0),
                    quality_level=self._determine_quality_level(assessment_data.get("overall_score", 0.0)),
                    metric_scores=assessment_data.get("metric_scores", {}),
                    validation_results=assessment_data.get("validation_results", []),
                    recommendations=assessment_data.get("recommendations", []),
                    assessed_at=datetime.now()
                )
        else:
            # Process sequentially
            for entity_id in entity_ids:
                try:
                    results[entity_id] = self.assess_data_quality(entity_type, entity_id)
                except Exception as e:
                    logger.error(f"Failed to assess {entity_type} {entity_id}: {str(e)}")
                    continue
        
        return results
    
    def monitor_quality_trends(self, entity_type: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Monitor data quality trends over time
        
        Args:
            entity_type: Type of entities to monitor
            days_back: Number of days to look back
            
        Returns:
            Quality trend analysis
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Get quality assessment history
        workflow.add_node("QualityHistoryQueryNode", "get_history", {
            "entity_type": entity_type,
            "start_date": datetime.now() - timedelta(days=days_back),
            "end_date": datetime.now(),
            "include_metric_breakdown": True
        })
        
        # Step 2: Analyze trends
        workflow.add_node("QualityTrendAnalysisNode", "analyze_trends", {
            "analysis_dimensions": [
                "overall_score_trend", "metric_trends",
                "quality_distribution", "common_issues",
                "improvement_areas"
            ]
        })
        workflow.add_connection("get_history", "quality_history", "analyze_trends", "historical_data")
        
        # Step 3: Generate insights
        workflow.add_node("QualityInsightGeneratorNode", "generate_insights", {
            "insight_categories": [
                "trend_insights", "pattern_detection",
                "anomaly_identification", "improvement_recommendations"
            ]
        })
        workflow.add_connection("analyze_trends", "trend_analysis", "generate_insights", "trends")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "entity_type": entity_type,
            "period_days": days_back,
            "trend_analysis": results.get("analyze_trends", {}),
            "insights": results.get("generate_insights", {}),
            "generated_at": datetime.now()
        }
    
    def setup_quality_alerts(self, alert_config: Dict[str, Any]) -> str:
        """
        Setup automated quality monitoring alerts
        
        Args:
            alert_config: Alert configuration
            
        Returns:
            Alert setup ID
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Create alert configuration
        workflow.add_node("QualityAlertSetupNode", "setup_alerts", {
            "alert_types": alert_config.get("alert_types", ["quality_degradation", "validation_failures"]),
            "thresholds": alert_config.get("thresholds", {}),
            "notification_methods": alert_config.get("notification_methods", ["email"]),
            "monitoring_frequency": alert_config.get("frequency", "daily")
        })
        
        # Step 2: Schedule monitoring
        workflow.add_node("MonitoringSchedulerNode", "schedule_monitoring", {
            "schedule_type": "recurring",
            "monitoring_workflow": "quality_assessment_monitoring"
        })
        workflow.add_connection("setup_alerts", "alert_config", "schedule_monitoring", "config")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return results.get("schedule_monitoring", {}).get("monitoring_id", "")
    
    def generate_quality_report(
        self, 
        entity_type: str, 
        report_scope: str = "comprehensive",
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report
        
        Args:
            entity_type: Type of entities to report on
            report_scope: basic, standard, comprehensive
            include_trends: Whether to include trend analysis
            
        Returns:
            Comprehensive quality report
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Get current quality status
        workflow.add_node("QualityStatusSummaryNode", "status_summary", {
            "entity_type": entity_type,
            "summary_scope": report_scope,
            "include_distribution": True
        })
        
        # Step 2: Get quality trends (if requested)
        if include_trends:
            workflow.add_node("QualityTrendReportNode", "trend_report", {
                "entity_type": entity_type,
                "trend_period_days": 90,
                "include_forecasting": report_scope == "comprehensive"
            })
        
        # Step 3: Identify top issues
        workflow.add_node("QualityIssueIdentificationNode", "identify_issues", {
            "entity_type": entity_type,
            "issue_categories": ["critical", "high", "medium"],
            "prioritization_method": "impact_frequency"
        })
        
        # Step 4: Generate improvement recommendations
        workflow.add_node("QualityImprovementRecommendationNode", "improvement_recommendations", {
            "entity_type": entity_type,
            "recommendation_scope": report_scope,
            "include_implementation_plan": report_scope == "comprehensive"
        })
        workflow.add_connection("identify_issues", "top_issues", "improvement_recommendations", "issues")
        
        # Step 5: Compile report
        workflow.add_node("QualityReportCompilerNode", "compile_report", {
            "report_format": "comprehensive",
            "include_charts": True,
            "include_executive_summary": True
        })
        workflow.add_connection("status_summary", "summary", "compile_report", "status_data")
        if include_trends:
            workflow.add_connection("trend_report", "trends", "compile_report", "trend_data")
        workflow.add_connection("identify_issues", "issues", "compile_report", "issues")
        workflow.add_connection("improvement_recommendations", "recommendations", "compile_report", "recommendations")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "report_type": "data_quality_report",
            "entity_type": entity_type,
            "report_scope": report_scope,
            "generated_at": datetime.now(),
            "report_data": results.get("compile_report", {}),
            "run_id": run_id
        }
    
    def _determine_quality_level(self, score: float) -> DataQualityLevel:
        """Determine quality level based on score"""
        if score >= 90:
            return DataQualityLevel.EXCELLENT
        elif score >= 75:
            return DataQualityLevel.GOOD
        elif score >= 60:
            return DataQualityLevel.FAIR
        elif score >= 40:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.CRITICAL
    
    def _get_completeness_criteria(self, entity_type: str) -> Dict[str, Any]:
        """Get completeness assessment criteria for entity type"""
        criteria_map = {
            "supplier_profile": {
                "required_fields": [
                    "supplier_id", "company_size", "primary_industries",
                    "geographic_coverage", "core_capabilities"
                ],
                "important_fields": [
                    "annual_revenue", "employee_count", "certifications",
                    "financial_rating", "delivery_zones"
                ],
                "optional_fields": [
                    "secondary_industries", "specialized_services",
                    "sustainability_practices"
                ]
            },
            "brand_intelligence": {
                "required_fields": [
                    "brand_id", "market_position", "target_market",
                    "quality_rating", "customer_satisfaction_score"
                ],
                "important_fields": [
                    "sustainability_rating", "warranty_terms",
                    "competitive_advantages", "pricing_strategy"
                ],
                "optional_fields": [
                    "innovation_score", "patent_portfolio_strength"
                ]
            }
        }
        return criteria_map.get(entity_type, {})
    
    def _get_consistency_rules(self, entity_type: str) -> List[str]:
        """Get consistency rules for entity type"""
        rules_map = {
            "supplier_profile": [
                "employee_count_vs_company_size",
                "revenue_vs_company_size",
                "geographic_coverage_vs_capabilities"
            ],
            "brand_intelligence": [
                "market_position_vs_pricing_strategy",
                "quality_rating_vs_customer_satisfaction",
                "innovation_score_vs_rd_investment"
            ]
        }
        return rules_map.get(entity_type, [])
    
    def _get_validation_sources(self, entity_type: str) -> List[str]:
        """Get external validation sources for accuracy checking"""
        sources_map = {
            "supplier_profile": [
                "business_registries", "financial_databases",
                "certification_authorities", "industry_directories"
            ],
            "brand_intelligence": [
                "market_research_firms", "industry_reports",
                "customer_review_platforms", "financial_databases"
            ]
        }
        return sources_map.get(entity_type, [])
    
    def _get_freshness_requirements(self, entity_type: str) -> Dict[str, int]:
        """Get data freshness requirements (in days) for entity type"""
        freshness_map = {
            "supplier_profile": {
                "basic_info": 365,      # Annual update
                "financial_data": 90,    # Quarterly update
                "certifications": 180,   # Bi-annual check
                "performance_metrics": 30 # Monthly update
            },
            "market_intelligence": {
                "pricing_data": 1,       # Daily update
                "availability": 7,       # Weekly update
                "demand_patterns": 30,   # Monthly analysis
                "competitive_data": 60   # Bi-monthly update
            }
        }
        return freshness_map.get(entity_type, {})

# Export the main class and enums
__all__ = ['DataQualityMonitoringSystem', 'DataQualityLevel', 'ValidationStatus', 'QualityAssessmentResult']