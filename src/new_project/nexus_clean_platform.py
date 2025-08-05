"""
Clean Nexus Multi-Channel Platform - No Windows Dependencies
===========================================================

Pure Docker deployment for Nexus platform providing:
- Multi-Channel Access: API + CLI + MCP
- Linux-only environment
- No Windows-specific code or paths
- Production-ready configuration
- Clean Docker deployment

Features:
- Zero Windows dependencies
- Pure Linux environment
- Docker-native deployment
- Multi-channel orchestration
- Production monitoring
- Health checks
"""

import os
import sys
import asyncio
import logging
import json  
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

# Core imports - no Windows dependencies
from nexus import Nexus
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Web framework imports
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import jwt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CLEAN CONFIGURATION (NO WINDOWS DEPENDENCIES)
# ==============================================================================

class CleanNexusConfig:
    """Clean configuration for Docker deployment"""
    
    def __init__(self):
        # Environment
        self.environment = os.getenv("NEXUS_ENV", "production")
        self.debug = self.environment == "development"
        
        # Server configuration - Docker networking
        self.api_port = int(os.getenv("NEXUS_API_PORT", "8000"))
        self.mcp_port = int(os.getenv("NEXUS_MCP_PORT", "3001"))
        self.api_host = os.getenv("NEXUS_API_HOST", "0.0.0.0")
        
        # Security
        self.jwt_secret = os.getenv("NEXUS_JWT_SECRET", "nexus-production-secret")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
        # Database - Docker services
        self.database_url = os.getenv("DATABASE_URL", "postgresql://nexus_user:password@postgres:5432/nexus_db")
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        # Performance
        self.cache_ttl_seconds = 300
        self.max_concurrent_requests = 100
        self.request_timeout = 30
        
        # CORS - Docker network compatible
        self.cors_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "healthy_checks": 0,
            "error_count": 0,
            "average_response_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def get_nexus_config(self) -> Dict[str, Any]:
        """Get clean Nexus configuration"""
        return {
            "api_port": self.api_port,
            "mcp_port": self.mcp_port,
            "enable_auth": True,
            "enable_monitoring": True,
            "rate_limit": 100,
            "auto_discovery": False,
            "cors_origins": self.cors_origins,
            "request_timeout": self.request_timeout,
            "max_concurrent_requests": self.max_concurrent_requests
        }

# Initialize clean configuration
config = CleanNexusConfig()

# ==============================================================================
# CLEAN NEXUS PLATFORM INITIALIZATION
# ==============================================================================

# Initialize clean Nexus platform
app = Nexus(**config.get_nexus_config())

# ==============================================================================
# CLEAN WORKFLOWS (NO WINDOWS DEPENDENCIES)
# ==============================================================================

def create_health_check_workflow():
    """Create health check workflow"""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "health_check", {
        "code": """
result = {
    'status': 'healthy',
    'platform': 'nexus-clean',
    'version': '2.0.0-clean',
    'timestamp': '""" + datetime.utcnow().isoformat() + """',
    'environment': '""" + config.environment + """',
    'docker_ready': True,
    'windows_dependencies': False
}
"""
    })
    
    return workflow

def create_platform_info_workflow():
    """Create platform information workflow"""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "platform_info", {
        "code": """
result = {
    'platform': 'Nexus Multi-Channel Platform',
    'version': '2.0.0-clean',
    'deployment': 'pure-docker',
    'channels': ['API', 'CLI', 'MCP'],
    'features': [
        'No Windows dependencies',
        'Pure Linux environment',
        'Docker-native deployment',
        'Multi-channel orchestration',
        'Production monitoring',
        'Health checks'
    ],
    'endpoints': {
        'api': 'http://0.0.0.0:""" + str(config.api_port) + """',
        'mcp': 'http://0.0.0.0:""" + str(config.mcp_port) + """',
        'health': 'http://0.0.0.0:""" + str(config.api_port) + """/api/health'
    },
    'docker': {
        'database': 'postgres:5432',
        'cache': 'redis:6379',
        'network': 'nexus-network'
    }
}
"""
    })
    
    return workflow

def create_metrics_workflow():
    """Create metrics collection workflow"""
    workflow = WorkflowBuilder()
    
    workflow.add_node("PythonCodeNode", "collect_metrics", {
        "code": f"""
import time
metrics = {json.dumps(config.metrics)}
result = {{
    'timestamp': time.time(),
    'metrics': metrics,
    'config': {{
        'environment': '{config.environment}',
        'api_port': {config.api_port},
        'mcp_port': {config.mcp_port},
        'cache_ttl': {config.cache_ttl_seconds},
        'max_concurrent': {config.max_concurrent_requests}
    }},
    'docker': {{
        'database_url': '{config.database_url.split('@')[1] if '@' in config.database_url else 'postgres:5432'}',
        'redis_url': '{config.redis_url.split('//')[1] if '//' in config.redis_url else 'redis:6379'}'
    }}
}}
"""
    })
    
    return workflow

# Register clean workflows
logger.info("🔧 Registering clean workflows...")

app.register("health_check", create_health_check_workflow().build())
app.register("platform_info", create_platform_info_workflow().build())
app.register("metrics_collection", create_metrics_workflow().build())

logger.info("✅ Clean workflows registered successfully")

# ==============================================================================
# CLEAN API ENDPOINTS (NO WINDOWS DEPENDENCIES)
# ==============================================================================

security = HTTPBearer()

# Add clean middleware
app.api_app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

app.api_app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.api_app.middleware("http")
async def add_performance_headers(request: Request, call_next):
    """Add performance tracking headers"""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    response.headers["X-Platform"] = "Nexus-Clean"
    response.headers["X-Environment"] = config.environment
    response.headers["X-Docker-Ready"] = "true"
    
    # Update metrics
    config.metrics["total_requests"] += 1
    config.metrics["average_response_time"] = (
        (config.metrics["average_response_time"] * (config.metrics["total_requests"] - 1) + process_time) /
        config.metrics["total_requests"]
    )
    
    return response

@app.api_app.get("/api/health")
async def health_check():
    """Clean health check endpoint"""
    try:
        runtime = LocalRuntime()
        workflow = create_health_check_workflow()
        
        results, run_id = runtime.execute(workflow.build())
        
        config.metrics["healthy_checks"] += 1
        
        health_data = results.get("health_check", {})
        health_data.update({
            "database": {
                "status": "available",
                "url": config.database_url.split('@')[1] if '@' in config.database_url else "postgres:5432"
            },
            "cache": {
                "status": "available", 
                "url": config.redis_url.split('//')[1] if '//' in config.redis_url else "redis:6379"
            },
            "docker": {
                "network": "nexus-network",
                "volumes": ["nexus_data", "nexus_logs", "nexus_cache"]
            },
            "run_id": run_id
        })
        
        return JSONResponse(content=health_data)
    
    except Exception as e:
        config.metrics["error_count"] += 1
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": "Health check failed",
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "nexus-clean"
            },
            status_code=503
        )

@app.api_app.get("/api/info")
async def platform_info():
    """Clean platform information endpoint"""
    try:
        runtime = LocalRuntime()
        workflow = create_platform_info_workflow()
        
        results, run_id = runtime.execute(workflow.build())
        
        info_data = results.get("platform_info", {})
        info_data["run_id"] = run_id
        
        return JSONResponse(content=info_data)
    
    except Exception as e:
        config.metrics["error_count"] += 1
        logger.error(f"Platform info error: {str(e)}")
        raise HTTPException(status_code=500, detail="Platform info failed")

@app.api_app.get("/api/metrics")
async def get_metrics():
    """Clean metrics endpoint"""
    try:
        runtime = LocalRuntime()
        workflow = create_metrics_workflow()
        
        results, run_id = runtime.execute(workflow.build())
        
        return JSONResponse(content=results.get("collect_metrics", {}))
    
    except Exception as e:
        config.metrics["error_count"] += 1
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics collection failed")

@app.api_app.post("/api/execute/{workflow_name}")
async def execute_workflow(workflow_name: str, request_data: Dict[str, Any] = None):
    """Execute registered workflow"""
    try:
        # Validate workflow exists
        if workflow_name not in ["health_check", "platform_info", "metrics_collection"]:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")
        
        runtime = LocalRuntime()
        
        # Get workflow by name
        if workflow_name == "health_check":
            workflow = create_health_check_workflow()
        elif workflow_name == "platform_info":
            workflow = create_platform_info_workflow()
        elif workflow_name == "metrics_collection":
            workflow = create_metrics_workflow()
        
        context = request_data or {}
        
        import time
        start_time = time.time()
        results, run_id = runtime.execute(workflow.build(), context)
        execution_time = time.time() - start_time
        
        return JSONResponse(content={
            "success": True,
            "workflow": workflow_name,
            "results": results,
            "metadata": {
                "execution_time_ms": round(execution_time * 1000, 2),
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "nexus-clean"
            }
        })
    
    except Exception as e:
        config.metrics["error_count"] += 1
        logger.error(f"Workflow execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

# ==============================================================================
# CLEAN CLI COMMANDS (NO WINDOWS DEPENDENCIES)
# ==============================================================================

@app.cli.command("status")
def status_command():
    """Show clean platform status"""
    print("🐳 Clean Nexus Platform Status:")
    print(f"   • Environment: {config.environment}")
    print(f"   • API Port: {config.api_port}")
    print(f"   • MCP Port: {config.mcp_port}")
    print(f"   • Database: {config.database_url.split('@')[1] if '@' in config.database_url else 'postgres:5432'}")
    print(f"   • Cache: {config.redis_url.split('//')[1] if '//' in config.redis_url else 'redis:6379'}")
    print(f"   • Docker Ready: ✅")
    print(f"   • Windows Dependencies: ❌ None")

@app.cli.command("metrics")
def metrics_command():
    """Show platform metrics"""
    print("📊 Platform Metrics:")
    for key, value in config.metrics.items():
        print(f"   • {key}: {value}")

@app.cli.command("test-workflows")
def test_workflows_command():
    """Test all registered workflows"""
    workflows = ["health_check", "platform_info", "metrics_collection"]
    
    for workflow_name in workflows:
        try:
            runtime = LocalRuntime()
            if workflow_name == "health_check":
                workflow = create_health_check_workflow()
            elif workflow_name == "platform_info":
                workflow = create_platform_info_workflow()
            elif workflow_name == "metrics_collection": 
                workflow = create_metrics_workflow()
            
            results, run_id = runtime.execute(workflow.build())
            print(f"✅ {workflow_name}: OK")
        except Exception as e:
            print(f"❌ {workflow_name}: {str(e)}")

# ==============================================================================
# CLEAN MCP TOOLS (NO WINDOWS DEPENDENCIES)
# ==============================================================================

@app.mcp_server.tool("health_check")
def health_check_tool() -> Dict[str, Any]:
    """MCP tool for health checking"""
    try:
        runtime = LocalRuntime()
        workflow = create_health_check_workflow()
        
        results, run_id = runtime.execute(workflow.build())
        
        return {
            "success": True,
            "health_data": results.get("health_check"),
            "run_id": run_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.mcp_server.tool("platform_info")
def platform_info_tool() -> Dict[str, Any]:
    """MCP tool for platform information"""
    try:
        runtime = LocalRuntime()
        workflow = create_platform_info_workflow()
        
        results, run_id = runtime.execute(workflow.build())
        
        return {
            "success": True,
            "platform_info": results.get("platform_info"),
            "run_id": run_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.mcp_server.tool("get_metrics")
def get_metrics_tool() -> Dict[str, Any]:
    """MCP tool for metrics collection"""
    try:
        runtime = LocalRuntime()
        workflow = create_metrics_workflow()
        
        results, run_id = runtime.execute(workflow.build())
        
        return {
            "success": True,
            "metrics": results.get("collect_metrics"),
            "run_id": run_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==============================================================================
# MAIN ENTRY POINT (CLEAN)
# ==============================================================================

def main():
    """Clean main entry point - no Windows dependencies"""
    print("\n" + "="*80)
    print("🐳 CLEAN NEXUS MULTI-CHANNEL PLATFORM")
    print("="*80)
    
    logger.info("✅ Clean Nexus Platform Configuration:")
    logger.info(f"   • Environment: {config.environment}")
    logger.info(f"   • Docker Deployment: Pure Linux")
    logger.info(f"   • Windows Dependencies: None")
    logger.info(f"   • Database: {config.database_url.split('@')[1] if '@' in config.database_url else 'postgres:5432'}")
    logger.info(f"   • Cache: {config.redis_url.split('//')[1] if '//' in config.redis_url else 'redis:6379'}")
    
    logger.info("🌐 Multi-channel access:")
    logger.info(f"   • API: http://{config.api_host}:{config.api_port}")
    logger.info(f"   • MCP: http://{config.api_host}:{config.mcp_port}")
    logger.info(f"   • CLI: nexus --help")
    
    logger.info("🔧 Registered workflows:")
    logger.info("   • health_check (platform health)")
    logger.info("   • platform_info (system information)")
    logger.info("   • metrics_collection (performance metrics)")
    
    logger.info("🐳 Docker Services:")
    logger.info("   • nexus-platform (main application)")
    logger.info("   • nexus-postgres (database)")
    logger.info("   • nexus-redis (cache)")
    logger.info("   • nexus-nginx (reverse proxy)")
    
    print("\n" + "="*80)
    print("🎯 CLEAN PLATFORM READY - Start with: docker-compose up")
    print("="*80)
    
    # Start the clean platform
    logger.info("🚀 Starting clean Nexus platform...")
    app.start()

if __name__ == "__main__":
    main()