"""
Semantic Knowledge Graph Implementation for Horme POV

This module implements a comprehensive semantic knowledge graph system for product relationships,
semantic search, and intelligent recommendations using Neo4j and vector embeddings.

Key Components:
- Neo4j knowledge graph for product relationships
- Vector embeddings for semantic similarity
- Relationship inference algorithms
- Integration with existing DataFlow PostgreSQL system

Architecture:
- PostgreSQL: Structured product data (existing)
- Neo4j: Graph relationships and semantic connections
- ChromaDB/Vector Search: Semantic embeddings and similarity
- Relationship Engine: AI-powered relationship inference
"""

__version__ = "1.0.0"
__author__ = "Horme POV Team"

from .database import Neo4jConnection, GraphDatabase
from .models import ProductNode, RelationshipType, SemanticRelationship
from .inference import RelationshipInferenceEngine
from .search import SemanticSearchEngine
from .integration import PostgreSQLIntegration

__all__ = [
    "Neo4jConnection",
    "GraphDatabase", 
    "ProductNode",
    "RelationshipType",
    "SemanticRelationship",
    "RelationshipInferenceEngine",
    "SemanticSearchEngine",
    "PostgreSQLIntegration"
]