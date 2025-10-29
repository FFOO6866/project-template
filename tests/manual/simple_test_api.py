"""
Simple Test API for Docker Environment
Tests basic connectivity to PostgreSQL and Redis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncpg
import redis.asyncio as redis
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Horme POV Test API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get connection details from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "horme-postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "horme_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "horme_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nexus_secure_password_2025")

REDIS_HOST = os.getenv("REDIS_HOST", "horme-redis-alt")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Horme POV Test API is running",
        "status": "operational",
        "endpoints": {
            "/": "This endpoint",
            "/health": "Health check",
            "/test-postgres": "Test PostgreSQL connection",
            "/test-redis": "Test Redis connection",
            "/docs": "API documentation"
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "api": "running",
        "postgres": "unknown",
        "redis": "unknown"
    }
    
    # Test PostgreSQL
    try:
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=int(POSTGRES_PORT),
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        health_status["postgres"] = "connected"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        health_status["postgres"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    # Test Redis
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()
        health_status["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/test-postgres")
async def test_postgres():
    """Test PostgreSQL connection and basic operations"""
    try:
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=int(POSTGRES_PORT),
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        
        # Get PostgreSQL version
        version = await conn.fetchval("SELECT version()")
        
        # List tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            LIMIT 10
        """)
        
        await conn.close()
        
        return {
            "status": "success",
            "connection": {
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "database": POSTGRES_DB,
                "user": POSTGRES_USER
            },
            "version": version,
            "tables": [t["tablename"] for t in tables]
        }
    except Exception as e:
        logger.error(f"PostgreSQL test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-redis")
async def test_redis():
    """Test Redis connection and basic operations"""
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        
        # Test basic operations
        await redis_client.set("test_key", "Hello from Docker!")
        value = await redis_client.get("test_key")
        
        # Get Redis info
        info = await redis_client.info("server")
        
        await redis_client.delete("test_key")
        await redis_client.close()
        
        return {
            "status": "success",
            "connection": {
                "host": REDIS_HOST,
                "port": REDIS_PORT
            },
            "test_value": value,
            "redis_version": info.get("redis_version", "unknown")
        }
    except Exception as e:
        logger.error(f"Redis test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)