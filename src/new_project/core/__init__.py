"""
Core business logic package.

This package contains the core business logic for the hybrid AI system:
- models/: Data models for knowledge graph, vector database, OpenAI, and hybrid recommendations
- services/: Business logic services for each component
"""

# Import base models and services if they exist
try:
    from .models import BaseModel
    from .services import BaseService
    base_imports = ["BaseModel", "BaseService"]
except ImportError:
    base_imports = []

__all__ = base_imports