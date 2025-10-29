"""
AI Context Injection System
Intelligent context injection for enhanced RFP processing, quotations, and work recommendations
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

from src.models.production_models import db
from src.models.supplier_intelligence_models import (
    SupplierProfile, SupplierPerformanceMetrics, BrandIntelligence, BrandProductLineIntelligence
)
from src.models.ai_context_models import (
    ProductIntelligence, ProductCompatibilityMatrix, UseCaseIntelligence
)
from src.models.market_intelligence_models import (
    MarketIntelligence, CompetitorIntelligence, MarketTrend, PricingIntelligence
)

class AIContextInjectionSystem:
    """System for injecting rich supplier/brand intelligence into AI workflows"""
    
    def __init__(self):
        self.runtime = LocalRuntime()
    
    def enhance_rfp_processing(self, rfp_id: int, context_depth: str = "comprehensive") -> Dict[str, Any]:
        """
        Enhanced RFP processing with supplier/brand intelligence context
        
        Args:
            rfp_id: RFP document ID to process
            context_depth: basic, standard, comprehensive
            
        Returns:
            Enhanced RFP analysis with supplier/brand context
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Get RFP document
        workflow.add_node("RFPDocumentReadNode", "get_rfp", {
            "id": rfp_id
        })
        
        # Step 2: Enhanced requirement analysis with AI context
        workflow.add_node("EnhancedRequirementAnalysisNode", "analyze_requirements", {
            "analysis_depth": context_depth,
            "include_technical_context": True,
            "include_supplier_context": True,
            "include_market_context": True
        })
        workflow.add_connection("get_rfp", "parsed_content", "analyze_requirements", "rfp_content")
        
        # Step 3: Get relevant use case intelligence
        workflow.add_node("UseCaseIntelligenceListNode", "get_use_cases", {
            "filter": {
                "use_case_category": {"$in": ["construction", "manufacturing", "office", "industrial"]},
                "market_frequency": {"$in": ["common", "very_common"]}
            },
            "limit": 20
        })
        workflow.add_connection("analyze_requirements", "identified_categories", "get_use_cases", "categories")
        
        # Step 4: Intelligent product matching with context
        workflow.add_node("IntelligentProductMatchingNode", "match_products", {
            "matching_algorithm": "hybrid_ai",
            "include_compatibility": True,
            "include_alternatives": True,
            "confidence_threshold": 0.7
        })
        workflow.add_connection("analyze_requirements", "technical_requirements", "match_products", "requirements")
        workflow.add_connection("get_use_cases", "use_cases", "match_products", "use_case_context")
        
        # Step 5: Get product intelligence for matched products
        workflow.add_node("ProductIntelligenceBatchLookupNode", "get_product_intel", {
            "include_compatibility_matrix": True,
            "include_use_case_scenarios": True,
            "intelligence_depth": context_depth
        })
        workflow.add_connection("match_products", "matched_product_ids", "get_product_intel", "product_ids")
        
        # Step 6: Supplier capability assessment
        workflow.add_node("SupplierCapabilityAssessmentNode", "assess_suppliers", {
            "assessment_criteria": [
                "geographic_coverage", "technical_capabilities", 
                "quality_rating", "delivery_performance",
                "financial_stability", "industry_experience"
            ],
            "include_performance_metrics": True
        })
        workflow.add_connection("match_products", "supplier_ids", "assess_suppliers", "supplier_ids")
        workflow.add_connection("analyze_requirements", "project_requirements", "assess_suppliers", "requirements")
        
        # Step 7: Brand intelligence integration
        workflow.add_node("BrandIntelligenceIntegrationNode", "integrate_brand_intel", {
            "integration_scope": [
                "quality_assessment", "market_position",
                "compatibility_analysis", "support_quality"
            ]
        })
        workflow.add_connection("match_products", "brand_ids", "integrate_brand_intel", "brand_ids")
        workflow.add_connection("get_product_intel", "intelligence_data", "integrate_brand_intel", "product_intelligence")
        
        # Step 8: Market intelligence context
        workflow.add_node("MarketIntelligenceContextNode", "market_context", {
            "context_elements": [
                "pricing_trends", "availability_status",
                "demand_patterns", "competitive_landscape",
                "supply_chain_risks"
            ]
        })
        workflow.add_connection("match_products", "product_supplier_pairs", "market_context", "product_supplier_pairs")
        
        # Step 9: Risk assessment with intelligence
        workflow.add_node("IntelligentRiskAssessmentNode", "assess_risks", {
            "risk_categories": [
                "supplier_risk", "product_risk", "market_risk",
                "technical_risk", "delivery_risk", "quality_risk"
            ],
            "risk_scoring_model": "comprehensive"
        })
        workflow.add_connection("assess_suppliers", "supplier_assessments", "assess_risks", "supplier_data")
        workflow.add_connection("integrate_brand_intel", "brand_assessments", "assess_risks", "brand_data")
        workflow.add_connection("market_context", "market_intelligence", "assess_risks", "market_data")
        
        # Step 10: Generate enhanced recommendations
        workflow.add_node("EnhancedRecommendationGeneratorNode", "generate_recommendations", {
            "recommendation_types": [
                "optimal_product_mix", "supplier_selection",
                "risk_mitigation", "cost_optimization",
                "timeline_optimization", "quality_assurance"
            ],
            "include_alternatives": True,
            "include_justifications": True
        })
        workflow.add_connection("get_product_intel", "intelligence_data", "generate_recommendations", "product_intelligence")
        workflow.add_connection("assess_suppliers", "supplier_assessments", "generate_recommendations", "supplier_intelligence")
        workflow.add_connection("integrate_brand_intel", "brand_assessments", "generate_recommendations", "brand_intelligence")
        workflow.add_connection("market_context", "market_intelligence", "generate_recommendations", "market_intelligence")
        workflow.add_connection("assess_risks", "risk_assessments", "generate_recommendations", "risk_data")
        
        # Step 11: Create enhanced RFP analysis
        workflow.add_node("EnhancedRFPAnalysisCreateNode", "create_analysis", {
            "analysis_completeness_threshold": 0.8,
            "include_confidence_scores": True
        })
        workflow.add_connection("generate_recommendations", "recommendations", "create_analysis", "recommendations")
        workflow.add_connection("assess_risks", "risk_assessments", "create_analysis", "risk_analysis")
        workflow.add_connection("market_context", "market_intelligence", "create_analysis", "market_context")
        workflow.add_connection("get_rfp", "id", "create_analysis", "rfp_id")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "success": True,
            "rfp_id": rfp_id,
            "enhanced_analysis": results,
            "run_id": run_id,
            "context_depth": context_depth
        }
    
    def enhance_quotation_generation(self, rfp_id: int, client_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent quotations with supplier/brand context
        
        Args:
            rfp_id: RFP document ID
            client_requirements: Specific client requirements
            
        Returns:
            Enhanced quotation with intelligent product selection and pricing
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Get enhanced RFP analysis
        workflow.add_node("RFPDocumentReadNode", "get_rfp_analysis", {
            "id": rfp_id,
            "include_analysis": True
        })
        
        # Step 2: Intelligent product selection with optimization
        workflow.add_node("IntelligentProductSelectionNode", "select_products", {
            "selection_criteria": [
                "requirement_match", "quality_score", "price_competitiveness",
                "supplier_reliability", "availability", "compatibility"
            ],
            "optimization_goals": ["cost", "quality", "delivery_time", "risk"],
            "include_alternatives": True
        })
        workflow.add_connection("get_rfp_analysis", "analysis_results", "select_products", "rfp_analysis")
        
        # Step 3: Volume discount optimization
        workflow.add_node("VolumeDiscountOptimizationNode", "optimize_discounts", {
            "optimization_strategy": "maximize_savings",
            "consider_supplier_tiers": True,
            "include_bundle_discounts": True
        })
        workflow.add_connection("select_products", "selected_products", "optimize_discounts", "product_list")
        
        # Step 4: Supplier negotiation intelligence
        workflow.add_node("SupplierNegotiationIntelligenceNode", "negotiation_intel", {
            "intelligence_aspects": [
                "negotiation_flexibility", "discount_patterns",
                "relationship_strength", "competitive_pressure",
                "volume_leverage"
            ]
        })
        workflow.add_connection("select_products", "supplier_ids", "negotiation_intel", "supplier_ids")
        
        # Step 5: Pricing intelligence integration
        workflow.add_node("PricingIntelligenceIntegrationNode", "pricing_intelligence", {
            "pricing_strategies": [
                "market_competitive", "value_based", "cost_plus",
                "relationship_pricing", "volume_discounting"
            ],
            "include_market_trends": True
        })
        workflow.add_connection("select_products", "product_supplier_pairs", "pricing_intelligence", "product_supplier_pairs")
        workflow.add_connection("negotiation_intel", "negotiation_data", "pricing_intelligence", "negotiation_context")
        
        # Step 6: Delivery optimization with supplier intelligence
        workflow.add_node("DeliveryOptimizationNode", "optimize_delivery", {
            "optimization_factors": [
                "supplier_location", "lead_times", "shipping_methods",
                "consolidation_opportunities", "rush_capabilities"
            ]
        })
        workflow.add_connection("select_products", "selected_products", "optimize_delivery", "products")
        workflow.add_connection("negotiation_intel", "supplier_capabilities", "optimize_delivery", "supplier_data")
        
        # Step 7: Quality assurance recommendations
        workflow.add_node("QualityAssuranceRecommendationNode", "quality_assurance", {
            "qa_aspects": [
                "supplier_quality_history", "brand_reliability",
                "inspection_requirements", "warranty_terms",
                "compliance_verification"
            ]
        })
        workflow.add_connection("select_products", "brand_ids", "quality_assurance", "brand_ids")
        workflow.add_connection("negotiation_intel", "supplier_quality_data", "quality_assurance", "supplier_quality")
        
        # Step 8: Risk mitigation strategies
        workflow.add_node("RiskMitigationStrategyNode", "risk_mitigation", {
            "mitigation_strategies": [
                "supplier_diversification", "inventory_buffering",
                "alternative_sourcing", "quality_controls",
                "delivery_insurance"
            ]
        })
        workflow.add_connection("pricing_intelligence", "risk_factors", "risk_mitigation", "identified_risks")
        
        # Step 9: Generate quotation line items with intelligence
        workflow.add_node("IntelligentQuotationGeneratorNode", "generate_quotation", {
            "line_item_optimization": True,
            "include_alternatives": True,
            "include_justifications": True,
            "pricing_strategy": "value_maximization"
        })
        workflow.add_connection("optimize_discounts", "optimized_pricing", "generate_quotation", "pricing_data")
        workflow.add_connection("optimize_delivery", "delivery_plan", "generate_quotation", "delivery_data")
        workflow.add_connection("quality_assurance", "qa_recommendations", "generate_quotation", "quality_data")
        workflow.add_connection("risk_mitigation", "mitigation_strategies", "generate_quotation", "risk_mitigation")
        
        # Step 10: Create quotation with intelligence context
        workflow.add_node("QuotationCreateNode", "create_quotation", {
            "include_intelligence_summary": True,
            "include_supplier_profiles": True,
            "include_risk_assessment": True
        })
        workflow.add_connection("generate_quotation", "quotation_data", "create_quotation", "quotation_data")
        workflow.add_connection("get_rfp_analysis", "id", "create_quotation", "rfp_id")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "success": True,
            "rfp_id": rfp_id,
            "quotation": results,
            "run_id": run_id,
            "intelligence_applied": True
        }
    
    def enhance_work_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent work recommendations with supplier/brand context
        
        Args:
            context: Context information (project type, budget, timeline, etc.)
            
        Returns:
            Enhanced work recommendations with intelligent supplier/brand selection
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Analyze work context and requirements
        workflow.add_node("WorkContextAnalysisNode", "analyze_context", {
            "analysis_dimensions": [
                "project_type", "complexity_level", "budget_constraints",
                "timeline_requirements", "quality_expectations",
                "skill_requirements", "safety_considerations"
            ]
        })
        
        # Step 2: Match relevant use case intelligence
        workflow.add_node("UseCaseMatchingNode", "match_use_cases", {
            "matching_algorithm": "semantic_similarity",
            "include_industry_context": True,
            "confidence_threshold": 0.6
        })
        workflow.add_connection("analyze_context", "analyzed_requirements", "match_use_cases", "requirements")
        
        # Step 3: Get products for use cases with intelligence
        workflow.add_node("UseCase2ProductMappingNode", "map_products", {
            "mapping_depth": "comprehensive",
            "include_alternatives": True,
            "include_compatibility": True
        })
        workflow.add_connection("match_use_cases", "matched_use_cases", "map_products", "use_cases")
        
        # Step 4: Product intelligence enrichment
        workflow.add_node("ProductIntelligenceEnrichmentNode", "enrich_products", {
            "enrichment_aspects": [
                "installation_complexity", "skill_requirements",
                "safety_considerations", "maintenance_needs",
                "performance_expectations"
            ]
        })
        workflow.add_connection("map_products", "product_ids", "enrich_products", "product_ids")
        workflow.add_connection("analyze_context", "context_requirements", "enrich_products", "context")
        
        # Step 5: Supplier capability assessment for recommendations
        workflow.add_node("RecommendationSupplierAssessmentNode", "assess_suppliers", {
            "assessment_focus": [
                "project_suitability", "capability_match",
                "geographic_alignment", "support_quality",
                "relationship_potential"
            ]
        })
        workflow.add_connection("map_products", "supplier_ids", "assess_suppliers", "supplier_ids")
        workflow.add_connection("analyze_context", "project_context", "assess_suppliers", "project_requirements")
        
        # Step 6: Brand intelligence for recommendations
        workflow.add_node("RecommendationBrandAssessmentNode", "assess_brands", {
            "assessment_criteria": [
                "quality_reputation", "user_experience",
                "support_quality", "innovation_level",
                "market_position"
            ]
        })
        workflow.add_connection("map_products", "brand_ids", "assess_brands", "brand_ids")
        workflow.add_connection("analyze_context", "quality_expectations", "assess_brands", "quality_requirements")
        
        # Step 7: Market intelligence for timing and availability
        workflow.add_node("RecommendationMarketIntelligenceNode", "market_intel", {
            "intelligence_focus": [
                "availability_forecast", "pricing_trends",
                "demand_patterns", "seasonal_factors",
                "supply_chain_stability"
            ]
        })
        workflow.add_connection("map_products", "product_supplier_pairs", "market_intel", "product_supplier_pairs")
        workflow.add_connection("analyze_context", "timeline_requirements", "market_intel", "timing_context")
        
        # Step 8: Intelligent recommendation scoring
        workflow.add_node("IntelligentRecommendationScoringNode", "score_recommendations", {
            "scoring_factors": [
                "requirement_match", "supplier_capability",
                "brand_quality", "market_viability",
                "risk_level", "cost_effectiveness"
            ],
            "scoring_model": "weighted_multi_criteria"
        })
        workflow.add_connection("enrich_products", "enriched_products", "score_recommendations", "products")
        workflow.add_connection("assess_suppliers", "supplier_assessments", "score_recommendations", "suppliers")
        workflow.add_connection("assess_brands", "brand_assessments", "score_recommendations", "brands")
        workflow.add_connection("market_intel", "market_intelligence", "score_recommendations", "market_data")
        
        # Step 9: Generate intelligent work recommendations
        workflow.add_node("IntelligentWorkRecommendationGeneratorNode", "generate_recommendations", {
            "recommendation_categories": [
                "optimal_approach", "product_selection",
                "supplier_recommendations", "timing_optimization",
                "risk_mitigation", "cost_optimization"
            ],
            "include_implementation_guide": True,
            "include_alternatives": True
        })
        workflow.add_connection("score_recommendations", "scored_recommendations", "generate_recommendations", "recommendations")
        workflow.add_connection("analyze_context", "project_context", "generate_recommendations", "context")
        
        # Step 10: Create work recommendation records
        workflow.add_node("WorkRecommendationBulkCreateNode", "create_recommendations", {
            "include_intelligence_context": True,
            "confidence_scoring": True,
            "priority_assignment": True
        })
        workflow.add_connection("generate_recommendations", "recommendations", "create_recommendations", "data")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return {
            "success": True,
            "context": context,
            "recommendations": results,
            "run_id": run_id,
            "intelligence_enhanced": True
        }
    
    def get_contextual_product_recommendations(
        self, 
        requirements: Dict[str, Any], 
        context_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contextual product recommendations based on requirements
        
        Args:
            requirements: Product requirements and constraints
            context_filters: Additional context filters
            
        Returns:
            List of contextual product recommendations with intelligence
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Analyze requirements with AI context
        workflow.add_node("RequirementAnalysisNode", "analyze_requirements", {
            "analysis_depth": "comprehensive",
            "include_implicit_requirements": True
        })
        
        # Step 2: Find compatible products with intelligence
        workflow.add_node("ProductIntelligenceListNode", "find_products", {
            "filter": {
                "use_case_scenarios": {"$elemMatch": {"$in": requirements.get("use_cases", [])}},
                "verification_status": "verified",
                "intelligence_completeness": {"$gte": 0.7}
            },
            "order_by": ["-intelligence_completeness", "-customer_satisfaction_score"],
            "limit": 50
        })
        
        # Step 3: Apply compatibility matrix intelligence
        workflow.add_node("CompatibilityMatrixFilterNode", "apply_compatibility", {
            "compatibility_threshold": 0.7,
            "include_synergies": True
        })
        workflow.add_connection("find_products", "products", "apply_compatibility", "products")
        
        # Step 4: Enrich with market intelligence
        workflow.add_node("MarketIntelligenceEnrichmentNode", "enrich_market", {
            "enrichment_scope": [
                "current_pricing", "availability_status",
                "lead_times", "supplier_reliability"
            ]
        })
        workflow.add_connection("apply_compatibility", "compatible_products", "enrich_market", "products")
        
        # Step 5: Generate contextual scores
        workflow.add_node("ContextualScoringNode", "contextual_scoring", {
            "scoring_dimensions": [
                "requirement_match", "quality_score", "value_score",
                "availability_score", "supplier_score", "risk_score"
            ],
            "weighting_strategy": "adaptive"
        })
        workflow.add_connection("enrich_market", "enriched_products", "contextual_scoring", "products")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return results.get("contextual_scoring", {}).get("recommendations", [])
    
    def get_supplier_intelligence_summary(self, supplier_ids: List[int]) -> Dict[str, Any]:
        """
        Get comprehensive supplier intelligence summary
        
        Args:
            supplier_ids: List of supplier IDs
            
        Returns:
            Comprehensive supplier intelligence summary
        """
        workflow = WorkflowBuilder()
        
        # Step 1: Get supplier profiles
        workflow.add_node("SupplierProfileListNode", "get_profiles", {
            "filter": {"supplier_id": {"$in": supplier_ids}},
            "limit": len(supplier_ids)
        })
        
        # Step 2: Get performance metrics
        workflow.add_node("SupplierPerformanceMetricsListNode", "get_metrics", {
            "filter": {"supplier_id": {"$in": supplier_ids}},
            "order_by": ["-measurement_period_end"],
            "limit": len(supplier_ids)
        })
        
        # Step 3: Generate intelligence summary
        workflow.add_node("SupplierIntelligenceSummaryNode", "generate_summary", {
            "summary_aspects": [
                "capability_overview", "performance_trends",
                "risk_assessment", "relationship_recommendations",
                "competitive_positioning"
            ]
        })
        workflow.add_connection("get_profiles", "profiles", "generate_summary", "profiles")
        workflow.add_connection("get_metrics", "metrics", "generate_summary", "metrics")
        
        # Execute workflow
        results, run_id = self.runtime.execute(workflow.build())
        
        return results.get("generate_summary", {})

# Export the main class
__all__ = ['AIContextInjectionSystem']