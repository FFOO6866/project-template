#!/usr/bin/env python3
"""
Test Data Initialization Script
==============================

Initializes all test databases with comprehensive data for testing.
Populates PostgreSQL, Neo4j, and ChromaDB with realistic test data.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import asyncpg
import chromadb
import numpy as np
import psycopg2
import redis
from neo4j import GraphDatabase

# Add test data factory to path
sys.path.append('/app/test-data')
from test_data_factory import (
    generate_all_test_data,
    ProductDataFactory,
    KnowledgeGraphDataFactory,
    PerformanceTestDataFactory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestDataInitializer:
    """Initialize all test databases with data"""
    
    def __init__(self):
        self.postgres_url = os.getenv('POSTGRES_URL', 'postgresql://test_user:test_pass@postgres-test:5432/horme_test')
        self.neo4j_url = os.getenv('NEO4J_URL', 'bolt://neo4j:test_password@neo4j-test:7687')
        self.chromadb_url = os.getenv('CHROMADB_URL', 'http://chromadb-test:8000')
        self.chromadb_token = os.getenv('CHROMADB_TOKEN', 'test-token')
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis-test:6379')
        
    async def wait_for_services(self, max_retries: int = 30):
        """Wait for all services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        services = {
            'postgres': self._check_postgres,
            'neo4j': self._check_neo4j, 
            'chromadb': self._check_chromadb,
            'redis': self._check_redis
        }
        
        for service_name, check_func in services.items():
            for attempt in range(max_retries):
                try:
                    await check_func()
                    logger.info(f"{service_name} is ready")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{service_name} failed to start after {max_retries} attempts: {e}")
                        raise
                    logger.info(f"Waiting for {service_name}... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2)
    
    async def _check_postgres(self):
        """Check PostgreSQL connectivity"""
        conn = await asyncpg.connect(self.postgres_url)
        await conn.execute('SELECT 1')
        await conn.close()
    
    async def _check_neo4j(self):
        """Check Neo4j connectivity"""
        driver = GraphDatabase.driver(self.neo4j_url)
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
    
    async def _check_chromadb(self):
        """Check ChromaDB connectivity"""
        client = chromadb.HttpClient(
            host=self.chromadb_url.replace('http://', '').split(':')[0],
            port=int(self.chromadb_url.split(':')[-1]),
            settings={
                "chroma_client_auth_provider": "token",
                "chroma_client_auth_credentials": self.chromadb_token
            }
        )
        client.heartbeat()
    
    async def _check_redis(self):
        """Check Redis connectivity"""
        r = redis.from_url(self.redis_url)
        r.ping()
        r.close()
    
    async def initialize_postgres(self):
        """Initialize PostgreSQL with test data"""
        logger.info("Initializing PostgreSQL test data...")
        
        # Generate test data
        products = ProductDataFactory.create_products(1000)
        users = ProductDataFactory.create_user_profiles(100)
        safety_standards = ProductDataFactory.create_safety_standards(50)
        
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Insert products
            product_data = [
                (
                    p.product_code, p.name, p.category, p.subcategory,
                    p.unspsc_code, p.etim_class, p.price, p.description,
                    p.safety_standards, p.vendor_id, p.skill_level_required,
                    p.complexity_score, p.embedding_vector
                )
                for p in products
            ]
            
            await conn.executemany("""
                INSERT INTO test_products (
                    product_code, name, category, subcategory, unspsc_code,
                    etim_class, price, description, safety_standards, vendor_id,
                    skill_level_required, complexity_score, embedding_vector
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (product_code) DO NOTHING
            """, product_data)
            
            # Insert users
            user_data = [
                (
                    u.user_id, u.username, u.email, u.role, u.skill_level,
                    u.experience_years, u.certifications, u.safety_training,
                    u.preferred_categories, u.location
                )
                for u in users
            ]
            
            await conn.executemany("""
                INSERT INTO test_users (
                    user_id, username, email, role, skill_level, experience_years,
                    certifications, safety_training, preferred_categories, location
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (username) DO NOTHING
            """, user_data)
            
            # Insert safety standards
            safety_data = [
                (
                    s.standard_id, s.name, s.organization, s.category,
                    s.description, s.requirements, s.applicable_products,
                    s.compliance_level
                )
                for s in safety_standards
            ]
            
            await conn.executemany("""
                INSERT INTO test_safety_standards (
                    standard_id, name, organization, category, description,
                    requirements, applicable_products, compliance_level
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (standard_id) DO NOTHING
            """, safety_data)
            
            logger.info(f"Inserted {len(products)} products, {len(users)} users, {len(safety_standards)} safety standards")
            
        finally:
            await conn.close()
    
    async def initialize_neo4j(self):
        """Initialize Neo4j with knowledge graph data"""
        logger.info("Initializing Neo4j knowledge graph...")
        
        driver = GraphDatabase.driver(self.neo4j_url)
        
        # Read and execute Cypher initialization script
        cypher_script_path = Path('/app/test-data/neo4j/init-knowledge-graph.cypher')
        if cypher_script_path.exists():
            with open(cypher_script_path, 'r') as f:
                cypher_script = f.read()
            
            # Split script into individual statements
            statements = [stmt.strip() for stmt in cypher_script.split(';') if stmt.strip()]
            
            with driver.session() as session:
                for statement in statements:
                    if statement and not statement.startswith('//'):
                        try:
                            session.run(statement)
                        except Exception as e:
                            logger.warning(f"Cypher statement failed (continuing): {e}")
            
            logger.info("Neo4j knowledge graph initialized")
        else:
            logger.warning("Neo4j initialization script not found")
        
        driver.close()
    
    async def initialize_chromadb(self):
        """Initialize ChromaDB with vector embeddings"""
        logger.info("Initializing ChromaDB vector database...")
        
        try:
            client = chromadb.HttpClient(
                host=self.chromadb_url.replace('http://', '').split(':')[0],
                port=int(self.chromadb_url.split(':')[-1]),
                settings={
                    "chroma_client_auth_provider": "token",
                    "chroma_client_auth_credentials": self.chromadb_token
                }
            )
            
            # Create collections for different types of embeddings
            collections = {
                'product_embeddings': 'Product descriptions and specifications',
                'safety_embeddings': 'Safety requirements and standards',
                'task_embeddings': 'Task descriptions and procedures'
            }
            
            for collection_name, description in collections.items():
                try:
                    collection = client.create_collection(
                        name=collection_name,
                        metadata={"description": description}
                    )
                    
                    # Generate sample embeddings
                    sample_size = 100
                    ids = [f"{collection_name}_{i:05d}" for i in range(sample_size)]
                    embeddings = np.random.normal(0, 1, (sample_size, 384)).tolist()
                    documents = [f"Sample document {i} for {collection_name}" for i in range(sample_size)]
                    metadatas = [{"index": i, "collection": collection_name} for i in range(sample_size)]
                    
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas
                    )
                    
                    logger.info(f"Created ChromaDB collection '{collection_name}' with {sample_size} embeddings")
                    
                except Exception as e:
                    if "already exists" in str(e):
                        logger.info(f"Collection '{collection_name}' already exists")
                    else:
                        logger.error(f"Failed to create collection '{collection_name}': {e}")
            
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
    
    async def initialize_redis(self):
        """Initialize Redis with cache data"""
        logger.info("Initializing Redis cache...")
        
        r = redis.from_url(self.redis_url)
        
        try:
            # Set up some test cache entries
            test_cache_data = {
                'test:product:popular': json.dumps(['PRD-00001', 'PRD-00002', 'PRD-00003']),
                'test:user:sessions:count': '0',
                'test:api:rate_limit:default': '1000',
                'test:search:recent_queries': json.dumps([
                    'drill bits', 'safety glasses', 'measuring tape'
                ])
            }
            
            for key, value in test_cache_data.items():
                r.setex(key, 3600, value)  # 1 hour TTL
            
            logger.info(f"Initialized Redis with {len(test_cache_data)} cache entries")
            
        finally:
            r.close()
    
    async def validate_initialization(self):
        """Validate that all data was initialized correctly"""
        logger.info("Validating test data initialization...")
        
        validation_results = {}
        
        # Validate PostgreSQL
        try:
            conn = await asyncpg.connect(self.postgres_url)
            product_count = await conn.fetchval("SELECT COUNT(*) FROM test_products")
            user_count = await conn.fetchval("SELECT COUNT(*) FROM test_users")
            safety_count = await conn.fetchval("SELECT COUNT(*) FROM test_safety_standards")
            await conn.close()
            
            validation_results['postgres'] = {
                'products': product_count,
                'users': user_count,
                'safety_standards': safety_count
            }
        except Exception as e:
            validation_results['postgres'] = f"Error: {e}"
        
        # Validate Neo4j
        try:
            driver = GraphDatabase.driver(self.neo4j_url)
            with driver.session() as session:
                tool_count = session.run("MATCH (t:Tool) RETURN count(t) as count").single()['count']
                task_count = session.run("MATCH (t:Task) RETURN count(t) as count").single()['count']
                relationship_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            driver.close()
            
            validation_results['neo4j'] = {
                'tools': tool_count,
                'tasks': task_count,
                'relationships': relationship_count
            }
        except Exception as e:
            validation_results['neo4j'] = f"Error: {e}"
        
        # Validate ChromaDB
        try:
            client = chromadb.HttpClient(
                host=self.chromadb_url.replace('http://', '').split(':')[0],
                port=int(self.chromadb_url.split(':')[-1]),
                settings={
                    "chroma_client_auth_provider": "token",
                    "chroma_client_auth_credentials": self.chromadb_token
                }
            )
            collections = client.list_collections()
            validation_results['chromadb'] = {
                'collections': len(collections),
                'collection_names': [c.name for c in collections]
            }
        except Exception as e:
            validation_results['chromadb'] = f"Error: {e}"
        
        # Validate Redis
        try:
            r = redis.from_url(self.redis_url)
            key_count = len(r.keys('test:*'))
            r.close()
            validation_results['redis'] = {'test_keys': key_count}
        except Exception as e:
            validation_results['redis'] = f"Error: {e}"
        
        logger.info("Validation results:")
        for service, results in validation_results.items():
            logger.info(f"  {service}: {results}")
        
        return validation_results


async def main():
    """Main initialization function"""
    logger.info("Starting test data initialization...")
    
    initializer = TestDataInitializer()
    
    try:
        # Wait for all services to be ready
        await initializer.wait_for_services()
        
        # Initialize each database
        await initializer.initialize_postgres()
        await initializer.initialize_neo4j()
        await initializer.initialize_chromadb()
        await initializer.initialize_redis()
        
        # Validate initialization
        validation_results = await initializer.validate_initialization()
        
        logger.info("Test data initialization completed successfully!")
        
        # Write validation results to file for CI/CD
        results_file = Path('/app/test-data/initialization_results.json')
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        return True
        
    except Exception as e:
        logger.error(f"Test data initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)