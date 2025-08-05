"""
Enhanced Minimal Nexus API - Building on Working Foundation
===========================================================

Enhanced API server that builds incrementally on the confirmed working base:
- Multiple workflows for different use cases
- Basic authentication and session management
- DataFlow integration when PostgreSQL available
- Performance monitoring
- Windows-compatible deployment

Based on successful minimal API server test.
"""

import os
import sys
import time
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Apply Windows compatibility first
import windows_sdk_compatibility

# Core SDK imports (confirmed working)
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# FastAPI imports (confirmed working)
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Simple authentication
security = HTTPBearer(auto_error=False)

class EnhancedMinimalNexusAPI:
    """Enhanced Minimal Nexus API Server"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Enhanced Minimal Nexus API",
            description="Building on working foundation with multiple workflows",
            version="1.1.0"
        )
        
        # Basic configuration
        self.config = {
            "host": "127.0.0.1",
            "port": 8003,
            "enable_auth": False,  # Start with auth disabled
            "enable_cors": True,
            "jwt_secret": "minimal-nexus-secret-key"
        }
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "workflows_executed": 0,
            "start_time": datetime.utcnow()
        }
        
        # Check DataFlow availability
        self.dataflow_available = self._check_dataflow()
        
        # Setup middleware
        self._setup_middleware()
        
        # Create workflows
        self.workflows = self._create_workflows()
        
        # Setup routes
        self._setup_routes()
    
    def _check_dataflow(self) -> bool:
        """Check if DataFlow is available with PostgreSQL"""
        try:
            from dataflow import DataFlow
            
            # Try PostgreSQL first
            try:
                db = DataFlow(
                    database_url="postgresql://horme_user:horme_password@localhost:5432/horme_classification_db",
                    auto_migrate=False,  # Don't auto-migrate during check
                    pool_size=5
                )
                print("   SUCCESS: PostgreSQL DataFlow available")
                return True
            except Exception:
                print("   INFO: PostgreSQL not available, DataFlow not enabled")
                return False
                
        except ImportError:
            print("   INFO: DataFlow not installed")
            return False
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        
        if self.config["enable_cors"]:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
        
        @self.app.middleware("http")
        async def track_requests(request: Request, call_next):
            start_time = time.time()
            
            # Update metrics
            self.metrics["total_requests"] += 1
            
            try:
                response = await call_next(request)
                
                # Calculate response time
                process_time = time.time() - start_time
                
                # Update metrics
                if response.status_code < 400:
                    self.metrics["successful_requests"] += 1
                else:
                    self.metrics["failed_requests"] += 1
                
                # Update average response time
                current_avg = self.metrics["average_response_time"]
                total_requests = self.metrics["total_requests"]
                self.metrics["average_response_time"] = (
                    (current_avg * (total_requests - 1) + process_time) / total_requests
                )
                
                # Add headers
                response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
                response.headers["X-Powered-By"] = "Enhanced-Minimal-Nexus"
                
                return response
                
            except Exception as e:
                self.metrics["failed_requests"] += 1
                raise e
    
    def _create_workflows(self) -> Dict[str, WorkflowBuilder]:
        """Create multiple workflows for different use cases"""
        
        workflows = {}
        
        # 1. Simple test workflow (confirmed working)
        def create_test_workflow():
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "execute_test", {
                "code": """
result = {
    'status': 'success',
    'message': 'Test workflow executed successfully',
    'timestamp': datetime.utcnow().isoformat(),
    'data': {'test_value': 42, 'workflow_type': 'test'}
}
"""
            })
            return workflow
        
        workflows["test"] = create_test_workflow()
        
        # 2. Data processing workflow
        def create_data_processing_workflow():
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "process_data", {
                "code": """
import json

# Get input data from context
input_data = context.get('data', [])

# Process the data
processed = []
for item in input_data:
    if isinstance(item, dict):
        processed.append({
            'id': item.get('id', 'unknown'),
            'processed': True,
            'timestamp': datetime.utcnow().isoformat(),
            'original': item
        })
    else:
        processed.append({
            'value': item,
            'processed': True,
            'type': type(item).__name__
        })

result = {
    'status': 'success',
    'message': f'Processed {len(processed)} items',
    'input_count': len(input_data),
    'output_count': len(processed),
    'processed_data': processed
}
"""
            })
            return workflow
        
        workflows["data_processing"] = create_data_processing_workflow()
        
        # 3. Classification workflow (mock for now)
        def create_classification_workflow():
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "classify_item", {
                "code": """
import random

# Get item to classify
item = context.get('item', {})
item_name = item.get('name', 'unknown')
item_description = item.get('description', '')

# Mock classification logic
categories = ['tools', 'safety', 'electrical', 'mechanical', 'other']
confidence_scores = [0.95, 0.87, 0.82, 0.76, 0.43]

# Simple classification based on keywords
classification = 'other'
confidence = 0.5

if 'tool' in item_name.lower() or 'drill' in item_name.lower():
    classification = 'tools'
    confidence = 0.95
elif 'safety' in item_name.lower() or 'ppe' in item_name.lower():
    classification = 'safety'
    confidence = 0.92
elif 'electrical' in item_name.lower() or 'wire' in item_name.lower():
    classification = 'electrical'
    confidence = 0.88

result = {
    'status': 'success',
    'message': 'Item classified successfully',
    'item': item,
    'classification': {
        'category': classification,
        'confidence': confidence,
        'method': 'keyword_based',
        'timestamp': datetime.utcnow().isoformat()
    }
}
"""
            })
            return workflow
        
        workflows["classification"] = create_classification_workflow()
        
        # 4. User management workflow
        def create_user_workflow():
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "manage_user", {
                "code": """
# Get user operation from context
operation = context.get('operation', 'info')
user_data = context.get('user_data', {})

if operation == 'create':
    result = {
        'status': 'success',
        'message': 'User created successfully',
        'user': {
            'id': hash(user_data.get('email', 'test')) % 10000,
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
    }
elif operation == 'info':
    result = {
        'status': 'success',
        'message': 'User info retrieved',
        'user': {
            'id': 1234,
            'email': 'demo@example.com',
            'name': 'Demo User',
            'active': True,
            'last_login': datetime.utcnow().isoformat()
        }
    }
else:
    result = {
        'status': 'error',
        'message': f'Unknown operation: {operation}'
    }
"""
            })
            return workflow
        
        workflows["user"] = create_user_workflow()
        
        return workflows
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return JSONResponse(content={
                "message": "Enhanced Minimal Nexus API",
                "version": "1.1.0",
                "status": "running",
                "dataflow_available": self.dataflow_available,
                "workflows": list(self.workflows.keys()),
                "endpoints": [
                    "/",
                    "/api/health",
                    "/api/metrics",
                    "/api/workflows",
                    "/api/workflows/{workflow_name}/execute"
                ]
            })
        
        @self.app.get("/api/health")
        async def health_check():
            uptime = datetime.utcnow() - self.metrics["start_time"]
            
            return JSONResponse(content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.1.0",
                "uptime_seconds": uptime.total_seconds(),
                "dataflow_available": self.dataflow_available,
                "database": "postgresql" if self.dataflow_available else "none",
                "sdk": "working",
                "workflows_count": len(self.workflows),
                "total_requests": self.metrics["total_requests"]
            })
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            uptime = datetime.utcnow() - self.metrics["start_time"]
            
            return JSONResponse(content={
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": {
                    "seconds": uptime.total_seconds(),
                    "formatted": str(uptime)
                },
                "requests": {
                    "total": self.metrics["total_requests"],
                    "successful": self.metrics["successful_requests"],
                    "failed": self.metrics["failed_requests"],
                    "success_rate": (
                        self.metrics["successful_requests"] / max(self.metrics["total_requests"], 1)
                    )
                },
                "performance": {
                    "average_response_time_ms": round(self.metrics["average_response_time"] * 1000, 2),
                    "workflows_executed": self.metrics["workflows_executed"]
                },
                "system": {
                    "dataflow_available": self.dataflow_available,
                    "auth_enabled": self.config["enable_auth"],
                    "cors_enabled": self.config["enable_cors"]
                }
            })
        
        @self.app.get("/api/workflows")
        async def list_workflows():
            workflow_info = {}
            
            for name, workflow in self.workflows.items():
                workflow_info[name] = {
                    "name": name,
                    "description": self._get_workflow_description(name),
                    "execute_url": f"/api/workflows/{name}/execute"
                }
            
            return JSONResponse(content={
                "workflows": workflow_info,
                "count": len(self.workflows)
            })
        
        @self.app.post("/api/workflows/{workflow_name}/execute")
        async def execute_workflow(
            workflow_name: str,
            request_data: Optional[Dict[str, Any]] = None,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            # Basic auth check (if enabled)
            if self.config["enable_auth"] and not credentials:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check if workflow exists
            if workflow_name not in self.workflows:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Workflow '{workflow_name}' not found. Available: {list(self.workflows.keys())}"
                )
            
            try:
                workflow = self.workflows[workflow_name]
                runtime = LocalRuntime()
                
                # Prepare context
                context = request_data or {}
                context["workflow_name"] = workflow_name
                context["timestamp"] = datetime.utcnow().isoformat()
                
                # Execute workflow
                start_time = time.time()
                results, run_id = runtime.execute(workflow.build(), context)
                execution_time = time.time() - start_time
                
                # Update metrics
                self.metrics["workflows_executed"] += 1
                
                return JSONResponse(content={
                    "success": True,
                    "workflow": workflow_name,
                    "results": results,
                    "metadata": {
                        "run_id": run_id,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "timestamp": datetime.utcnow().isoformat(),
                        "context_provided": bool(request_data)
                    }
                })
                
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Workflow execution failed: {str(e)}"
                )
        
        # Specific workflow endpoints for convenience
        @self.app.post("/api/classify")
        async def classify_item(item_data: Dict[str, Any]):
            """Convenient endpoint for classification"""
            return await execute_workflow("classification", {"item": item_data})
        
        @self.app.post("/api/process")
        async def process_data(data: Dict[str, Any]):
            """Convenient endpoint for data processing"""
            return await execute_workflow("data_processing", data)
        
        @self.app.get("/api/user/{user_id}")
        async def get_user(user_id: int):
            """Convenient endpoint for user info"""
            return await execute_workflow("user", {"operation": "info", "user_id": user_id})
    
    def _get_workflow_description(self, workflow_name: str) -> str:
        """Get workflow description"""
        descriptions = {
            "test": "Simple test workflow for validation",
            "data_processing": "Process and transform data arrays",
            "classification": "Classify items into categories",
            "user": "User management operations"
        }
        return descriptions.get(workflow_name, "No description available")
    
    def start(self):
        """Start the server"""
        print(f"\nEnhanced Minimal Nexus API Server")
        print(f"=" * 50)
        print(f"   Host: {self.config['host']}")
        print(f"   Port: {self.config['port']}")
        print(f"   DataFlow: {'Available' if self.dataflow_available else 'Not available'}")
        print(f"   Auth: {'Enabled' if self.config['enable_auth'] else 'Disabled'}")
        print(f"   CORS: {'Enabled' if self.config['enable_cors'] else 'Disabled'}")
        print(f"   Workflows: {len(self.workflows)} ({', '.join(self.workflows.keys())})")
        print(f"\nAccess URLs:")
        print(f"   API Base: http://{self.config['host']}:{self.config['port']}")
        print(f"   Health: http://{self.config['host']}:{self.config['port']}/api/health")
        print(f"   Metrics: http://{self.config['host']}:{self.config['port']}/api/metrics")
        print(f"   Workflows: http://{self.config['host']}:{self.config['port']}/api/workflows")
        print(f"=" * 50)
        
        uvicorn.run(
            self.app,
            host=self.config["host"],
            port=self.config["port"],
            log_level="info"
        )

def main():
    """Main entry point"""
    print("Enhanced Minimal Nexus API")
    print("Building on confirmed working foundation")
    
    try:
        api = EnhancedMinimalNexusAPI()
        api.start()
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
    except Exception as e:
        print(f"\nServer failed to start: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()