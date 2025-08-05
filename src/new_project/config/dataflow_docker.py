"""
DataFlow Docker Configuration for Production Containers
======================================================

Docker-optimized DataFlow configuration with:
- PostgreSQL service name (postgres:5432)
- Redis service name (redis:6379)
- Container-specific connection pooling
- Health check integration
- No Windows-specific paths

This configuration file is specifically designed for Docker environments
and replaces localhost with Docker service names.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataflow import DataFlow

def create_docker_dataflow_instance() -> DataFlow:
    """
    Create DataFlow instance optimized for Docker container deployment.
    
    Uses environment variables with Docker service name defaults:
    - DATABASE_URL: postgresql://horme_user:horme_password@postgres:5432/horme_classification_db
    - REDIS_URL: redis://redis:6379/2
    
    Returns:
        DataFlow: Configured instance ready for Docker container usage
    """
    
    # Docker service-based URLs (no localhost)
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://horme_user:horme_password@postgres:5432/horme_classification_db'
    )
    
    redis_url = os.getenv(
        'REDIS_URL', 
        'redis://redis:6379/2'  # Dedicated Redis DB for DataFlow classification
    )
    
    # Container-optimized connection pooling
    pool_size = int(os.getenv('DATAFLOW_POOL_SIZE', '75'))
    pool_max_overflow = int(os.getenv('DATAFLOW_MAX_OVERFLOW', '150'))
    pool_recycle = int(os.getenv('DATAFLOW_POOL_RECYCLE', '1200'))
    
    # Performance configuration from environment
    enable_monitoring = os.getenv('DATAFLOW_MONITORING', 'true').lower() == 'true'
    echo_sql = os.getenv('DATAFLOW_ECHO_SQL', 'false').lower() == 'true'
    auto_migrate = os.getenv('DATAFLOW_AUTO_MIGRATE', 'true').lower() == 'true'
    
    # Create DataFlow instance with Docker-optimized settings
    db = DataFlow(
        database_url=database_url,
        
        # Container-optimized connection pooling
        pool_size=pool_size,
        pool_max_overflow=pool_max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,              # Essential for container reliability
        pool_timeout=20,                 # Fast timeout for container environments
        pool_reset_on_return='rollback', # Clean state for classification transactions
        
        # Performance monitoring for containers
        monitoring=enable_monitoring,
        performance_tracking=True,
        slow_query_threshold=500,        # Log queries >500ms
        echo=echo_sql,                   # Configurable SQL logging
        
        # Auto-migration for container initialization
        auto_migrate=auto_migrate,
        migration_timeout=600,           # 10 minutes for complex schema setup
        
        # PostgreSQL extensions for classification (container-compatible)
        extensions=['pgvector', 'pg_trgm', 'btree_gin', 'pg_stat_statements', 'pgcrypto'],
        
        # Enterprise features for production containers
        enable_audit_log=True,
        enable_soft_delete=True,
        enable_versioning=True,
        
        # Redis caching with Docker service name
        enable_caching=True,
        cache_backend=redis_url,
        cache_prefix='classification',
        cache_compression='gzip',
        cache_serializer='msgpack',      # Efficient for container memory usage
        
        # Vector search optimization for containers
        enable_vector_indexing=True,
        vector_dimensions=1536,          # OpenAI embedding dimensions
        vector_index_type='ivfflat',     # Optimal for similarity search
        vector_lists=1000,               # Index parameter for 100k+ vectors
        
        # Bulk operation optimization for container workloads
        bulk_batch_size=8000,            # Optimal for container memory
        bulk_insert_method='copy',       # COPY for bulk data
        enable_bulk_upsert=True,
        
        # Query optimization for containers
        query_cache_size=15000,
        enable_prepared_statements=True,
        statement_cache_size=1000,
        
        # Container health and reliability
        health_check_interval=30,        # Frequent health checks for containers
        connection_invalidate_pool_on_disconnect=True,
        enable_connection_pooling_metrics=True
    )
    
    return db


def get_docker_database_url() -> str:
    """Get Docker-specific database URL with service name."""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://horme_user:horme_password@postgres:5432/horme_classification_db'
    )


def get_docker_redis_url() -> str:
    """Get Docker-specific Redis URL with service name."""
    return os.getenv('REDIS_URL', 'redis://redis:6379/2')


def validate_docker_connectivity() -> Dict[str, bool]:
    """
    Validate connectivity to Docker services.
    
    Returns:
        Dict[str, bool]: Service connectivity status
    """
    import asyncpg
    import redis
    
    results = {
        'postgresql': False,
        'redis': False
    }
    
    # Test PostgreSQL connectivity
    try:
        import asyncio
        
        async def test_postgres():
            try:
                conn = await asyncpg.connect(get_docker_database_url())
                await conn.close()
                return True
            except Exception:
                return False
        
        results['postgresql'] = asyncio.run(test_postgres())
    except Exception:
        results['postgresql'] = False
    
    # Test Redis connectivity
    try:
        r = redis.from_url(get_docker_redis_url())
        r.ping()
        results['redis'] = True
    except Exception:
        results['redis'] = False
    
    return results


def get_docker_health_check_queries() -> Dict[str, str]:
    """
    Get health check queries optimized for Docker containers.
    
    Returns:
        Dict[str, str]: Health check queries for each service
    """
    return {
        'postgresql': "SELECT 1 as health_check",
        'redis': "PING",
        'dataflow_models': """
            SELECT COUNT(*) as model_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('company', 'user', 'customer', 'quote')
        """,
        'dataflow_extensions': """
            SELECT extname 
            FROM pg_extension 
            WHERE extname IN ('pgvector', 'pg_trgm', 'btree_gin')
        """
    }


def setup_docker_environment_variables() -> Dict[str, str]:
    """
    Setup environment variables for Docker DataFlow configuration.
    
    Returns:
        Dict[str, str]: Environment variables for Docker deployment
    """
    return {
        # Database Configuration
        'DATABASE_URL': 'postgresql://horme_user:horme_password@postgres:5432/horme_classification_db',
        'REDIS_URL': 'redis://redis:6379/2',
        
        # DataFlow Configuration
        'DATAFLOW_POOL_SIZE': '75',
        'DATAFLOW_MAX_OVERFLOW': '150',
        'DATAFLOW_POOL_RECYCLE': '1200',
        'DATAFLOW_MONITORING': 'true',
        'DATAFLOW_ECHO_SQL': 'false',
        'DATAFLOW_AUTO_MIGRATE': 'true',
        
        # Performance Tuning
        'DATAFLOW_BULK_BATCH_SIZE': '8000',
        'DATAFLOW_CACHE_TTL': '2700',
        'DATAFLOW_QUERY_CACHE_SIZE': '15000',
        
        # Container Health
        'DATAFLOW_HEALTH_CHECK_INTERVAL': '30',
        'DATAFLOW_CONNECTION_TIMEOUT': '20',
        'DATAFLOW_MIGRATION_TIMEOUT': '600'
    }


# Export configured DataFlow instance for Docker usage
docker_db = create_docker_dataflow_instance()

# Export utility functions
__all__ = [
    'create_docker_dataflow_instance',
    'docker_db',
    'get_docker_database_url',
    'get_docker_redis_url', 
    'validate_docker_connectivity',
    'get_docker_health_check_queries',
    'setup_docker_environment_variables'
]