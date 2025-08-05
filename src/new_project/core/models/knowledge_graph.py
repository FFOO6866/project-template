"""
Knowledge Graph Data Models
===========================

Data models for Neo4j knowledge graph entities including tools, tasks, 
projects, users, and safety rules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class Tool:
    """Tool model for knowledge graph"""
    name: str
    category: str
    brand: str
    specifications: Dict[str, Any]
    safety_rating: float
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate tool data after initialization"""
        if not self.name or not self.name.strip():
            raise ValueError("Tool name cannot be empty")
        
        if not self.category or not self.category.strip():
            raise ValueError("Tool category cannot be empty")
            
        if not self.brand or not self.brand.strip():
            raise ValueError("Tool brand cannot be empty")
            
        if not isinstance(self.specifications, dict):
            raise ValueError("Tool specifications must be a dictionary")
            
        if not (0.0 <= self.safety_rating <= 5.0):
            raise ValueError("Safety rating must be between 0.0 and 5.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for Neo4j storage"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "brand": self.brand,
            "specifications": self.specifications,
            "safety_rating": self.safety_rating
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tool":
        """Create tool from dictionary"""
        return cls(
            id=data.get("id"),
            name=data["name"],
            category=data["category"],
            brand=data["brand"],
            specifications=data["specifications"],
            safety_rating=data["safety_rating"]
        )


@dataclass
class Task:
    """Task model for knowledge graph"""
    name: str
    complexity: int
    required_skills: List[str]
    estimated_time: int  # in minutes
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate task data after initialization"""
        if not self.name or not self.name.strip():
            raise ValueError("Task name cannot be empty")
            
        if not (1 <= self.complexity <= 10):
            raise ValueError("Task complexity must be between 1 and 10")
            
        if not self.required_skills or len(self.required_skills) == 0:
            raise ValueError("Task must have at least one required skill")
            
        if self.estimated_time <= 0:
            raise ValueError("Estimated time must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for Neo4j storage"""
        return {
            "id": self.id,
            "name": self.name,
            "complexity": self.complexity,
            "required_skills": self.required_skills,
            "estimated_time": self.estimated_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        return cls(
            id=data.get("id"),
            name=data["name"],
            complexity=data["complexity"],
            required_skills=data["required_skills"],
            estimated_time=data["estimated_time"]
        )


@dataclass
class Project:
    """Project model for knowledge graph"""
    name: str
    project_type: str
    difficulty_level: str
    estimated_duration: int  # in hours
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate project data after initialization"""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
            
        if not self.project_type or not self.project_type.strip():
            raise ValueError("Project type cannot be empty")
            
        if self.difficulty_level not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Difficulty level must be beginner, intermediate, or advanced")
            
        if self.estimated_duration <= 0:
            raise ValueError("Estimated duration must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for Neo4j storage"""
        return {
            "id": self.id,
            "name": self.name,
            "project_type": self.project_type,
            "difficulty_level": self.difficulty_level,
            "estimated_duration": self.estimated_duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create project from dictionary"""
        return cls(
            id=data.get("id"),
            name=data["name"],
            project_type=data["project_type"],
            difficulty_level=data["difficulty_level"],
            estimated_duration=data["estimated_duration"]
        )


@dataclass
class User:
    """User model for knowledge graph"""
    username: str
    skill_level: str
    experience: List[str]
    preferences: Dict[str, Any]
    safety_certification: List[str] = field(default_factory=list)
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate user data after initialization"""
        if not self.username or not self.username.strip():
            raise ValueError("Username cannot be empty")
            
        if self.skill_level not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Skill level must be beginner, intermediate, or advanced")
            
        if not isinstance(self.experience, list):
            raise ValueError("Experience must be a list")
            
        if not isinstance(self.preferences, dict):
            raise ValueError("Preferences must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for Neo4j storage"""
        return {
            "id": self.id,
            "username": self.username,
            "skill_level": self.skill_level,
            "experience": self.experience,
            "preferences": self.preferences,
            "safety_certification": self.safety_certification
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create user from dictionary"""
        return cls(
            id=data.get("id"),
            username=data["username"],
            skill_level=data["skill_level"],
            experience=data["experience"],
            preferences=data["preferences"],
            safety_certification=data.get("safety_certification", [])
        )


@dataclass
class SafetyRule:
    """Safety rule model for knowledge graph"""
    osha_code: str
    ansi_standard: str
    description: str
    severity: str
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validate safety rule data after initialization"""
        if not self.osha_code or not self.osha_code.strip():
            raise ValueError("OSHA code cannot be empty")
            
        if not self.ansi_standard or not self.ansi_standard.strip():
            raise ValueError("ANSI standard cannot be empty")
            
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
            
        if self.severity not in ["low", "medium", "high", "critical"]:
            raise ValueError("Severity must be low, medium, high, or critical")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert safety rule to dictionary for Neo4j storage"""
        return {
            "id": self.id,
            "osha_code": self.osha_code,
            "ansi_standard": self.ansi_standard,
            "description": self.description,
            "severity": self.severity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SafetyRule":
        """Create safety rule from dictionary"""
        return cls(
            id=data.get("id"),
            osha_code=data["osha_code"],
            ansi_standard=data["ansi_standard"],
            description=data["description"],
            severity=data["severity"]
        )