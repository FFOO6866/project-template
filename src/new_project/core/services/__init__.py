"""
Core Services Package
====================

Core services for the hybrid AI system including:
- Knowledge Graph Service (Neo4j)
- Vector Database Service (ChromaDB) 
- OpenAI Integration Service
- Hybrid Recommendation Pipeline
"""

from .knowledge_graph import KnowledgeGraphService, Neo4jSchema
from .vector_database import VectorDatabaseService, ChromaDBCollections
from .openai_integration import OpenAIIntegrationService, PromptTemplates
from .hybrid_recommendation_pipeline import HybridRecommendationPipeline, RecommendationEngine, ResultMerger

__all__ = [
    "KnowledgeGraphService",
    "Neo4jSchema", 
    "VectorDatabaseService",
    "ChromaDBCollections",
    "OpenAIIntegrationService",
    "PromptTemplates",
    "HybridRecommendationPipeline",
    "RecommendationEngine",
    "ResultMerger"
]