"""
Test Data Generation Factory for Testing Infrastructure
====================================================

Comprehensive test data generation utilities for all testing tiers.
Provides realistic data for products, users, safety standards, and knowledge graphs.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from faker import Faker
import numpy as np

fake = Faker()
fake.seed_instance(42)  # Reproducible test data


@dataclass
class Product:
    """Product data model for testing"""
    product_code: str
    name: str
    category: str
    subcategory: str
    unspsc_code: str
    etim_class: str
    price: float
    description: str
    safety_standards: List[str]
    vendor_id: str
    skill_level_required: str
    complexity_score: int
    embedding_vector: Optional[List[float]] = None


@dataclass
class UserProfile:
    """User profile data model for testing"""
    user_id: str
    username: str
    email: str
    role: str
    skill_level: str
    experience_years: int
    certifications: List[str]
    safety_training: List[str]
    preferred_categories: List[str]
    location: str
    created_at: datetime


@dataclass
class SafetyStandard:
    """Safety standard data model for testing"""
    standard_id: str
    name: str
    organization: str  # OSHA, ANSI, ISO, etc.
    category: str
    description: str
    requirements: List[str]
    applicable_products: List[str]
    compliance_level: str
    last_updated: datetime


@dataclass
class KnowledgeGraphNode:
    """Knowledge graph node for testing"""
    node_id: str
    node_type: str
    name: str
    properties: Dict[str, Any]
    
    
@dataclass
class KnowledgeGraphRelationship:
    """Knowledge graph relationship for testing"""
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any]


class ProductDataFactory:
    """Factory for generating realistic product test data"""
    
    # UNSPSC product categories and codes
    UNSPSC_CATEGORIES = {
        "25": "Manufacturing Components and Supplies",
        "27": "Pharmaceuticals and Medicine",  
        "31": "Manufacturing and Processing Machinery",
        "40": "Tools and General Machinery",
        "46": "Electronic Equipment and Components",
        "53": "Apparel and Luggage and Personal Care Products",
    }
    
    # ETIM classification codes
    ETIM_CLASSES = {
        "EC001234": "Power Tools - Drilling",
        "EC001235": "Power Tools - Cutting", 
        "EC001236": "Hand Tools - Measuring",
        "EC001237": "Safety Equipment - Personal Protection",
        "EC001238": "Fasteners - Screws and Bolts",
        "EC001239": "Electronic Components - Sensors",
    }
    
    TOOL_CATEGORIES = [
        "Power Tools", "Hand Tools", "Measuring Tools", "Safety Equipment",
        "Fasteners", "Electronic Components", "Pneumatic Tools", "Hydraulic Tools"
    ]
    
    SKILL_LEVELS = ["beginner", "intermediate", "advanced", "expert"]
    
    SAFETY_STANDARDS = [
        "OSHA-1910.95", "ANSI-Z87.1", "ISO-45001", "NFPA-70E",
        "ANSI-B11.1", "OSHA-1926.95", "ISO-12100", "ANSI-A10.3"
    ]
    
    @classmethod
    def create_products(cls, count: int = 100) -> List[Product]:
        """Generate realistic product data with UNSPSC codes"""
        products = []
        
        for i in range(count):
            unspsc_segment = random.choice(list(cls.UNSPSC_CATEGORIES.keys()))
            etim_class = random.choice(list(cls.ETIM_CLASSES.keys()))
            category = random.choice(cls.TOOL_CATEGORIES)
            skill_level = random.choice(cls.SKILL_LEVELS)
            
            # Generate embedding vector (384 dimensions for sentence transformers)
            embedding_vector = np.random.normal(0, 1, 384).tolist()
            
            product = Product(
                product_code=f"PRD-{i+1:05d}",
                name=fake.catch_phrase().replace(',', ''),
                category=category,
                subcategory=fake.word().title(),
                unspsc_code=f"{unspsc_segment}{random.randint(10, 99)}{random.randint(10, 99)}",
                etim_class=etim_class,
                price=round(random.uniform(10.99, 2999.99), 2),
                description=fake.text(max_nb_chars=200),
                safety_standards=random.sample(cls.SAFETY_STANDARDS, k=random.randint(1, 3)),
                vendor_id=f"VND-{random.randint(1, 50):03d}",
                skill_level_required=skill_level,
                complexity_score=random.randint(1, 10),
                embedding_vector=embedding_vector
            )
            products.append(product)
        
        return products
    
    @classmethod
    def create_safety_standards(cls, count: int = 50) -> List[SafetyStandard]:
        """Generate OSHA/ANSI safety standards"""
        standards = []
        organizations = ["OSHA", "ANSI", "ISO", "NFPA", "ASTM"]
        categories = ["Personal Protection", "Machine Safety", "Electrical Safety", 
                     "Chemical Safety", "Fire Safety", "Construction Safety"]
        compliance_levels = ["mandatory", "recommended", "advisory"]
        
        for i in range(count):
            org = random.choice(organizations)
            category = random.choice(categories)
            
            standard = SafetyStandard(
                standard_id=f"{org}-{random.randint(1000, 9999)}.{random.randint(1, 99)}",
                name=f"{category} Standard - {fake.catch_phrase()}",
                organization=org,
                category=category,
                description=fake.text(max_nb_chars=300),
                requirements=[fake.sentence() for _ in range(random.randint(3, 8))],
                applicable_products=[f"PRD-{random.randint(1, 100):05d}" for _ in range(random.randint(5, 15))],
                compliance_level=random.choice(compliance_levels),
                last_updated=fake.date_time_between(start_date='-2y', end_date='now')
            )
            standards.append(standard)
        
        return standards
    
    @classmethod
    def create_user_profiles(cls, count: int = 100) -> List[UserProfile]:
        """Generate user profiles with skill assessments"""
        profiles = []
        roles = ["user", "admin", "safety_officer", "procurement_specialist"]
        skill_levels = ["novice", "intermediate", "advanced", "expert"]
        certifications = ["OSHA-10", "OSHA-30", "CPR", "First Aid", "Forklift", "Crane Operator"]
        safety_training = ["Hazmat", "Confined Space", "Fall Protection", "Lockout/Tagout"]
        
        for i in range(count):
            profile = UserProfile(
                user_id=str(uuid.uuid4()),
                username=fake.user_name(),
                email=fake.email(),
                role=random.choice(roles),
                skill_level=random.choice(skill_levels),
                experience_years=random.randint(0, 30),
                certifications=random.sample(certifications, k=random.randint(1, 4)),
                safety_training=random.sample(safety_training, k=random.randint(1, 3)),
                preferred_categories=random.sample(cls.TOOL_CATEGORIES, k=random.randint(2, 4)),
                location=fake.city(),
                created_at=fake.date_time_between(start_date='-1y', end_date='now')
            )
            profiles.append(profile)
        
        return profiles


class KnowledgeGraphDataFactory:
    """Factory for generating knowledge graph test data"""
    
    NODE_TYPES = ["Tool", "Task", "Skill", "SafetyRequirement", "Material", "Process"]
    RELATIONSHIP_TYPES = ["USED_FOR", "REQUIRES", "PRODUCES", "CONNECTS_TO", "DEPENDS_ON", "SIMILAR_TO"]
    
    @classmethod
    def create_nodes(cls, count: int = 200) -> List[KnowledgeGraphNode]:
        """Generate knowledge graph nodes"""
        nodes = []
        
        for i in range(count):
            node_type = random.choice(cls.NODE_TYPES)
            
            properties = {
                "description": fake.text(max_nb_chars=100),
                "category": fake.word(),
                "created_at": fake.iso8601(),
                "importance_score": random.uniform(0.1, 1.0)
            }
            
            # Add type-specific properties
            if node_type == "Tool":
                properties.update({
                    "power_rating": f"{random.randint(100, 2000)}W",
                    "weight": f"{random.uniform(0.5, 15.0):.1f}kg",
                    "voltage": f"{random.choice([110, 220, 240])}V"
                })
            elif node_type == "Task":
                properties.update({
                    "complexity": random.choice(["low", "medium", "high"]),
                    "estimated_time": f"{random.randint(5, 120)}min",
                    "skill_required": random.choice(["beginner", "intermediate", "advanced"])
                })
            elif node_type == "SafetyRequirement":
                properties.update({
                    "standard": random.choice(ProductDataFactory.SAFETY_STANDARDS),
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "mandatory": random.choice([True, False])
                })
            
            node = KnowledgeGraphNode(
                node_id=f"{node_type.upper()}_{i+1:05d}",
                node_type=node_type,
                name=fake.catch_phrase().replace(',', ''),
                properties=properties
            )
            nodes.append(node)
        
        return nodes
    
    @classmethod
    def create_relationships(cls, nodes: List[KnowledgeGraphNode], 
                           relationship_count: int = 400) -> List[KnowledgeGraphRelationship]:
        """Generate relationships between nodes"""
        relationships = []
        node_ids = [node.node_id for node in nodes]
        
        for i in range(relationship_count):
            source_id = random.choice(node_ids)
            target_id = random.choice(node_ids)
            
            # Avoid self-relationships
            while target_id == source_id:
                target_id = random.choice(node_ids)
            
            relationship_type = random.choice(cls.RELATIONSHIP_TYPES)
            
            properties = {
                "strength": random.uniform(0.1, 1.0),
                "created_at": fake.iso8601(),
                "verified": random.choice([True, False]),
                "confidence": random.uniform(0.5, 1.0)
            }
            
            relationship = KnowledgeGraphRelationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                properties=properties
            )
            relationships.append(relationship)
        
        return relationships


class PerformanceTestDataFactory:
    """Factory for generating performance testing data"""
    
    @classmethod
    def create_load_test_data(cls, user_count: int = 100, 
                             request_count: int = 1000) -> Dict[str, Any]:
        """Generate data for load testing scenarios"""
        users = ProductDataFactory.create_user_profiles(user_count)
        products = ProductDataFactory.create_products(request_count)
        
        # Generate search queries for testing
        search_queries = []
        for _ in range(request_count):
            query_type = random.choice(["product_search", "recommendation", "safety_check"])
            
            if query_type == "product_search":
                query = {
                    "type": "search",
                    "query": fake.catch_phrase(),
                    "category": random.choice(ProductDataFactory.TOOL_CATEGORIES),
                    "max_price": random.randint(100, 1000)
                }
            elif query_type == "recommendation":
                query = {
                    "type": "recommendation",
                    "user_id": random.choice(users).user_id,
                    "product_category": random.choice(ProductDataFactory.TOOL_CATEGORIES),
                    "skill_level": random.choice(ProductDataFactory.SKILL_LEVELS)
                }  
            else:  # safety_check
                query = {
                    "type": "safety_check",
                    "product_id": random.choice(products).product_code,
                    "user_skill": random.choice(ProductDataFactory.SKILL_LEVELS),
                    "environment": random.choice(["indoor", "outdoor", "wet", "dry"])
                }
            
            search_queries.append(query)
        
        return {
            "users": [asdict(user) for user in users],
            "products": [asdict(product) for product in products],
            "search_queries": search_queries,
            "concurrent_users": user_count,
            "total_requests": request_count,
            "target_rps": 50,
            "duration_seconds": 300
        }


def generate_all_test_data(output_dir: str = "./test-data"):
    """Generate comprehensive test data and save to files"""
    import os
    import json
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate data
    products = ProductDataFactory.create_products(1000)
    users = ProductDataFactory.create_user_profiles(100)
    safety_standards = ProductDataFactory.create_safety_standards(50)
    kg_nodes = KnowledgeGraphDataFactory.create_nodes(200)
    kg_relationships = KnowledgeGraphDataFactory.create_relationships(kg_nodes, 400)
    load_test_data = PerformanceTestDataFactory.create_load_test_data(100, 1000)
    
    # Save to JSON files
    datasets = {
        "products.json": [asdict(p) for p in products],
        "users.json": [asdict(u) for u in users], 
        "safety_standards.json": [asdict(s) for s in safety_standards],
        "knowledge_graph_nodes.json": [asdict(n) for n in kg_nodes],
        "knowledge_graph_relationships.json": [asdict(r) for r in kg_relationships],
        "load_test_data.json": load_test_data
    }
    
    for filename, data in datasets.items():
        file_path = output_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        print(f"Generated {filename} with {len(data) if isinstance(data, list) else 'metadata'} records")
    
    return datasets


if __name__ == "__main__":
    # Generate test data when run directly
    generate_all_test_data()