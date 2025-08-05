"""
Vector Database Data Models
===========================

Data models for ChromaDB vector database entities including product embeddings,
manual embeddings, safety guideline embeddings, and project pattern embeddings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class ProductEmbedding:
    """Product embedding model for vector database"""
    product_code: str
    name: str
    description: str
    category: str
    embedding_vector: List[float]
    brand: Optional[str] = None
    price: Optional[float] = None
    specifications: Optional[Dict[str, Any]] = field(default_factory=dict)
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate product embedding data after initialization"""
        if not self.product_code or not self.product_code.strip():
            raise ValueError("Product code cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty")
            
        if not self.description or not self.description.strip():
            raise ValueError("Product description cannot be empty")
            
        if not self.category or not self.category.strip():
            raise ValueError("Product category cannot be empty")
            
        if not self.embedding_vector or len(self.embedding_vector) != 1536:
            raise ValueError("Embedding vector must have 1536 dimensions")
            
        if self.price is not None and self.price < 0:
            raise ValueError("Price must be non-negative")
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dictionary for ChromaDB storage"""
        metadata = {
            "product_code": self.product_code,
            "name": self.name,
            "category": self.category
        }
        
        if self.brand:
            metadata["brand"] = self.brand
        if self.price is not None:
            metadata["price"] = self.price
        if self.specifications:
            metadata["specifications"] = str(self.specifications)
            
        return metadata
    
    def to_document(self) -> str:
        """Convert to document text for ChromaDB storage"""
        document_parts = [self.name, self.description]
        if self.brand:
            document_parts.append(f"Brand: {self.brand}")
        if self.specifications:
            spec_text = " ".join([f"{k}: {v}" for k, v in self.specifications.items()])
            document_parts.append(f"Specifications: {spec_text}")
        
        return " | ".join(document_parts)


@dataclass
class ManualEmbedding:
    """Manual embedding model for vector database"""
    manual_id: str
    product_code: str
    section: str
    page_number: int
    content: str
    content_type: str
    embedding_vector: List[float]
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate manual embedding data after initialization"""
        if not self.manual_id or not self.manual_id.strip():
            raise ValueError("Manual ID cannot be empty")
            
        if not self.product_code or not self.product_code.strip():
            raise ValueError("Product code cannot be empty")
            
        if not self.section or not self.section.strip():
            raise ValueError("Section cannot be empty")
            
        if self.page_number <= 0:
            raise ValueError("Page number must be positive")
            
        if not self.content or not self.content.strip():
            raise ValueError("Content cannot be empty")
            
        if self.content_type not in ["instructions", "safety", "troubleshooting", "specifications", "warranty"]:
            raise ValueError("Content type must be valid type")
            
        if not self.embedding_vector or len(self.embedding_vector) != 1536:
            raise ValueError("Embedding vector must have 1536 dimensions")
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dictionary for ChromaDB storage"""
        return {
            "manual_id": self.manual_id,
            "product_code": self.product_code,
            "section": self.section,
            "page_number": self.page_number,
            "content_type": self.content_type
        }
    
    def to_document(self) -> str:
        """Convert to document text for ChromaDB storage"""
        return f"Section: {self.section} | Page: {self.page_number} | Content: {self.content}"


@dataclass
class SafetyEmbedding:
    """Safety guideline embedding model for vector database"""
    guideline_id: str
    osha_code: str
    ansi_standard: str
    title: str
    content: str
    severity: str
    category: str
    embedding_vector: List[float]
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate safety embedding data after initialization"""
        if not self.guideline_id or not self.guideline_id.strip():
            raise ValueError("Guideline ID cannot be empty")
            
        if not self.osha_code or not self.osha_code.strip():
            raise ValueError("OSHA code cannot be empty")
            
        if not self.ansi_standard or not self.ansi_standard.strip():
            raise ValueError("ANSI standard cannot be empty")
            
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
            
        if not self.content or not self.content.strip():
            raise ValueError("Content cannot be empty")
            
        if self.severity not in ["low", "medium", "high", "critical"]:
            raise ValueError("Severity must be low, medium, high, or critical")
            
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")
            
        if not self.embedding_vector or len(self.embedding_vector) != 1536:
            raise ValueError("Embedding vector must have 1536 dimensions")
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dictionary for ChromaDB storage"""
        return {
            "guideline_id": self.guideline_id,
            "osha_code": self.osha_code,
            "ansi_standard": self.ansi_standard,
            "severity": self.severity,
            "category": self.category
        }
    
    def to_document(self) -> str:
        """Convert to document text for ChromaDB storage"""
        return f"Title: {self.title} | OSHA: {self.osha_code} | ANSI: {self.ansi_standard} | Content: {self.content}"


@dataclass
class ProjectEmbedding:
    """Project pattern embedding model for vector database"""
    pattern_id: str
    project_type: str
    title: str
    description: str
    difficulty: str
    tools_required: List[str]
    estimated_time: int  # in minutes
    materials: List[str]
    embedding_vector: List[float]
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate project embedding data after initialization"""
        if not self.pattern_id or not self.pattern_id.strip():
            raise ValueError("Pattern ID cannot be empty")
            
        if not self.project_type or not self.project_type.strip():
            raise ValueError("Project type cannot be empty")
            
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
            
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
            
        if self.difficulty not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Difficulty must be beginner, intermediate, or advanced")
            
        if not self.tools_required or len(self.tools_required) == 0:
            raise ValueError("Must have at least one required tool")
            
        if self.estimated_time <= 0:
            raise ValueError("Estimated time must be positive")
            
        if not self.materials or len(self.materials) == 0:
            raise ValueError("Must have at least one material")
            
        if not self.embedding_vector or len(self.embedding_vector) != 1536:
            raise ValueError("Embedding vector must have 1536 dimensions")
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dictionary for ChromaDB storage"""
        return {
            "pattern_id": self.pattern_id,
            "project_type": self.project_type,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "tools_count": len(self.tools_required),
            "materials_count": len(self.materials)
        }
    
    def to_document(self) -> str:
        """Convert to document text for ChromaDB storage"""
        tools_text = ", ".join(self.tools_required)
        materials_text = ", ".join(self.materials)
        
        return (f"Title: {self.title} | Project Type: {self.project_type} | "
                f"Description: {self.description} | Tools: {tools_text} | "
                f"Materials: {materials_text} | Difficulty: {self.difficulty}")