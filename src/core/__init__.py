"""
Core Database Infrastructure
Direct implementation without SDK dependencies
Windows-compatible production system
"""

from .database import ProductDatabase, DatabaseConfig, get_database, close_database
from .business_logic import (
    ProductSearchEngine, RFPAnalyzer, WorkRecommendationEngine,
    SearchResult, RFPAnalysis, WorkRecommendation,
    get_search_engine, get_rfp_analyzer, get_recommendation_engine
)
from .api import app

__version__ = "1.0.0"
__all__ = [
    "ProductDatabase",
    "DatabaseConfig", 
    "get_database",
    "close_database",
    "ProductSearchEngine",
    "RFPAnalyzer", 
    "WorkRecommendationEngine",
    "SearchResult",
    "RFPAnalysis",
    "WorkRecommendation",
    "get_search_engine",
    "get_rfp_analyzer", 
    "get_recommendation_engine",
    "app"
]