"""
Core Models Package
==================

Data models for the hybrid AI system including:
- Knowledge Graph Models (Neo4j entities)
- Vector Database Models (ChromaDB entities)
- OpenAI Integration Models (Request/Response models)
- Hybrid Recommendation Models (Pipeline models)
- DataFlow Models (FOUND-003: Horme Product Ecosystem)
"""

from .knowledge_graph import Tool, Task, Project, User, SafetyRule
from .vector_database import ProductEmbedding, ManualEmbedding, SafetyEmbedding, ProjectEmbedding
from .openai_integration import (
    ToolRecommendationRequest, ToolRecommendationResponse,
    SafetyAssessmentRequest, SafetyAssessmentResponse,
    ProjectAnalysisRequest, ProjectAnalysisResponse
)
from .hybrid_recommendations import (
    HybridRecommendationRequest, HybridRecommendationResponse,
    ComponentScore, RecommendationResult, ConfidenceMetrics
)

# Import DataFlow models from parent models.py file
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    # Import from the models.py file in the parent core directory
    import importlib.util
    models_file = os.path.join(os.path.dirname(__file__), '..', 'models.py')
    spec = importlib.util.spec_from_file_location("dataflow_models", models_file)
    dataflow_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dataflow_models)
    
    # Import DataFlow models
    db = dataflow_models.db
    Product = dataflow_models.Product
    ProductCategory = dataflow_models.ProductCategory
    ProductSpecification = dataflow_models.ProductSpecification
    UNSPSCCode = dataflow_models.UNSPSCCode
    ETIMClass = dataflow_models.ETIMClass
    SafetyStandard = dataflow_models.SafetyStandard
    ComplianceRequirement = dataflow_models.ComplianceRequirement
    PPERequirement = dataflow_models.PPERequirement
    Vendor = dataflow_models.Vendor
    ProductPricing = dataflow_models.ProductPricing
    InventoryLevel = dataflow_models.InventoryLevel
    UserProfile = dataflow_models.UserProfile
    SkillAssessment = dataflow_models.SkillAssessment
    SafetyCertification = dataflow_models.SafetyCertification
    get_auto_generated_nodes = dataflow_models.get_auto_generated_nodes
    validate_model_integrity = dataflow_models.validate_model_integrity
    
except Exception as e:
    print(f"Warning: Could not import DataFlow models: {e}")
    # Create mock models for testing
    class MockModel:
        __dataflow__ = True
        __tablename__ = 'mock_table'
        
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class MockDB:
        def model(self, cls):
            cls.__dataflow__ = True
            return cls
    
    db = MockDB()
    Product = ProductCategory = ProductSpecification = MockModel
    UNSPSCCode = ETIMClass = MockModel
    SafetyStandard = ComplianceRequirement = PPERequirement = MockModel
    Vendor = ProductPricing = InventoryLevel = MockModel
    UserProfile = SkillAssessment = SafetyCertification = MockModel

__all__ = [
    # Knowledge Graph Models
    "Tool", "Task", "Project", "User", "SafetyRule",
    
    # Vector Database Models
    "ProductEmbedding", "ManualEmbedding", "SafetyEmbedding", "ProjectEmbedding",
    
    # OpenAI Integration Models
    "ToolRecommendationRequest", "ToolRecommendationResponse",
    "SafetyAssessmentRequest", "SafetyAssessmentResponse", 
    "ProjectAnalysisRequest", "ProjectAnalysisResponse",
    
    # Hybrid Recommendation Models
    "HybridRecommendationRequest", "HybridRecommendationResponse",
    "ComponentScore", "RecommendationResult", "ConfidenceMetrics",
    
    # DataFlow Models (FOUND-003)
    "db", "Product", "ProductCategory", "ProductSpecification",
    "UNSPSCCode", "ETIMClass", "SafetyStandard", "ComplianceRequirement", "PPERequirement",
    "Vendor", "ProductPricing", "InventoryLevel",
    "UserProfile", "SkillAssessment", "SafetyCertification",
    "get_auto_generated_nodes", "validate_model_integrity"
]