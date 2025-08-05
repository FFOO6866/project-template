# NEXUS-001: Multi-Channel Platform Setup

**Created:** 2025-08-02  
**Assigned:** Nexus Specialist + Platform Team  
**Priority:** 🚀 P1 - HIGH  
**Status:** PENDING  
**Estimated Effort:** 12 hours  
**Due Date:** 2025-08-09 (Week 3 - Platform Integration Phase)

## Description

Deploy Nexus platform for simultaneous API + CLI + MCP server deployment, enabling unified sessions across all access methods. This establishes the multi-channel foundation for the Kailash SDK implementation with seamless workflow execution across different interfaces.

## Strategic Context

Nexus provides the unified platform layer that allows the same workflows to be accessed through:
- **REST API**: For web applications and external integrations
- **CLI Interface**: For command-line tools and automation scripts  
- **MCP Server**: For AI assistant integration and real-time interactions

This multi-channel approach ensures consistent user experience and unified session management across all access patterns.

## Acceptance Criteria

- [ ] Nexus platform deployed with API + CLI + MCP server simultaneously
- [ ] Unified session management working across all three interfaces
- [ ] Workflow execution consistent across API, CLI, and MCP channels
- [ ] Authentication and authorization working for all access methods
- [ ] Real-time WebSocket endpoints configured for streaming responses
- [ ] Health monitoring and service discovery operational
- [ ] Configuration management for multi-environment deployment
- [ ] Load balancing and scalability features configured
- [ ] Error handling and logging consistent across all channels

## Subtasks

- [ ] Nexus Core Platform Setup (Est: 3h)
  - Verification: Nexus platform installed and core services running
  - Output: Multi-channel platform foundation with basic configuration

- [ ] API Endpoint Configuration (Est: 2h)
  - Verification: REST API endpoints accessible and responding correctly
  - Output: Complete API interface with authentication and basic workflows

- [ ] CLI Interface Implementation (Est: 2h)
  - Verification: Command-line interface can execute workflows and access all features
  - Output: Full CLI functionality with help system and command completion

- [ ] MCP Server Integration (Est: 3h)
  - Verification: MCP server running with AI assistant integration capabilities
  - Output: Real-time MCP interface with streaming response support

- [ ] Unified Session Management (Est: 1h)
  - Verification: Sessions persist and sync across API, CLI, and MCP interfaces
  - Output: Seamless user experience across all access methods

- [ ] Multi-Channel Testing and Validation (Est: 1h)
  - Verification: All interfaces work together without conflicts
  - Output: Comprehensive testing suite for multi-channel functionality

## Dependencies

- **FOUND-002**: Architecture Setup (multi-framework approach configured)
- **INFRA-004**: WSL2 + Docker Environment (for service infrastructure)
- **FOUND-001**: SDK Compliance Foundation (for workflow execution patterns)

## Risk Assessment

- **HIGH**: Complex multi-channel architecture may have interface conflicts
- **MEDIUM**: Session synchronization across channels may require careful state management
- **MEDIUM**: Authentication and authorization complexity across different access methods
- **LOW**: Performance overhead from managing multiple simultaneous interfaces

## Technical Implementation Plan

### Phase 3B-1: Nexus Core Platform Setup (Hours 1-3)
```python
# nexus_platform_config.py
from kailash.nexus import NexusPlatform
from kailash.nexus.config import PlatformConfig
from kailash.workflow.builder import WorkflowBuilder

class MultiChannelPlatformSetup:
    """Configure Nexus platform for API + CLI + MCP deployment"""
    
    def __init__(self):
        self.config = PlatformConfig(
            api_enabled=True,
            cli_enabled=True,
            mcp_enabled=True,
            websocket_enabled=True,
            session_sync=True
        )
        
        self.platform = NexusPlatform(self.config)
    
    def setup_platform(self):
        """Initialize complete multi-channel platform"""
        
        # Configure API endpoints
        self._setup_api_endpoints()
        
        # Configure CLI interface
        self._setup_cli_interface()
        
        # Configure MCP server
        self._setup_mcp_server()
        
        # Configure WebSocket for real-time features
        self._setup_websocket_handlers()
        
        # Configure unified sessions
        self._setup_session_management()
        
        return self.platform
    
    def _setup_api_endpoints(self):
        """Configure REST API endpoints"""
        
        # Classification workflow endpoints
        self.platform.add_api_endpoint(
            path="/api/v1/classify",
            method="POST",
            workflow_name="classification_workflow",
            description="Product classification using UNSPSC/ETIM standards"
        )
        
        # Recommendation workflow endpoints
        self.platform.add_api_endpoint(
            path="/api/v1/recommend",
            method="POST", 
            workflow_name="recommendation_workflow",
            description="AI-powered tool recommendations"
        )
        
        # Search and discovery endpoints
        self.platform.add_api_endpoint(
            path="/api/v1/search",
            method="GET",
            workflow_name="search_workflow",
            description="Semantic search across product catalog"
        )
        
        # Health and status endpoints
        self.platform.add_api_endpoint(
            path="/api/v1/health",
            method="GET",
            handler=self._health_check,
            description="Platform health and status"
        )
    
    def _setup_cli_interface(self):
        """Configure command-line interface"""
        
        # Classification commands
        self.platform.add_cli_command(
            command="classify",
            workflow_name="classification_workflow",
            description="Classify products using UNSPSC/ETIM",
            options=[
                {"name": "--input", "required": True, "help": "Product description or file"},
                {"name": "--format", "default": "json", "help": "Output format"},
                {"name": "--standards", "default": "both", "help": "UNSPSC, ETIM, or both"}
            ]
        )
        
        # Recommendation commands
        self.platform.add_cli_command(
            command="recommend",
            workflow_name="recommendation_workflow", 
            description="Get tool recommendations for projects",
            options=[
                {"name": "--project-type", "required": True, "help": "Type of project"},
                {"name": "--budget", "help": "Budget constraints"},
                {"name": "--safety-level", "help": "Required safety compliance level"}
            ]
        )
        
        # Search commands
        self.platform.add_cli_command(
            command="search",
            workflow_name="search_workflow",
            description="Search product catalog semantically",
            options=[
                {"name": "--query", "required": True, "help": "Search query"},
                {"name": "--limit", "default": 10, "help": "Number of results"},
                {"name": "--category", "help": "Limit to specific category"}
            ]
        )
    
    def _setup_mcp_server(self):
        """Configure MCP server for AI assistant integration"""
        
        # MCP tools for AI assistant
        self.platform.add_mcp_tool(
            name="classify_product",
            workflow_name="classification_workflow",
            description="Classify hardware products using industry standards",
            parameters={
                "product_description": {"type": "string", "required": True},
                "classification_standards": {"type": "array", "default": ["UNSPSC", "ETIM"]}
            }
        )
        
        self.platform.add_mcp_tool(
            name="recommend_tools",
            workflow_name="recommendation_workflow",
            description="Recommend tools and hardware for specific projects",
            parameters={
                "project_description": {"type": "string", "required": True},
                "budget_range": {"type": "object", "properties": {"min": "number", "max": "number"}},
                "safety_requirements": {"type": "array", "items": {"type": "string"}}
            }
        )
        
        self.platform.add_mcp_tool(
            name="search_products",
            workflow_name="search_workflow", 
            description="Search product catalog with semantic understanding",
            parameters={
                "search_query": {"type": "string", "required": True},
                "filters": {"type": "object", "properties": {"category": "string", "price_range": "object"}}
            }
        )
        
        # Real-time streaming support
        self.platform.configure_mcp_streaming(
            enabled=True,
            chunk_size=1024,
            timeout=30
        )
    
    def _setup_websocket_handlers(self):
        """Configure WebSocket endpoints for real-time features"""
        
        # Real-time classification progress
        self.platform.add_websocket_handler(
            path="/ws/classify",
            handler=self._handle_classification_stream,
            description="Real-time classification progress updates"
        )
        
        # Real-time recommendation updates
        self.platform.add_websocket_handler(
            path="/ws/recommend", 
            handler=self._handle_recommendation_stream,
            description="Streaming recommendation results"
        )
        
        # Chat interface for AI assistant
        self.platform.add_websocket_handler(
            path="/ws/chat",
            handler=self._handle_chat_stream,
            description="Real-time chat with AI assistant"
        )
    
    def _setup_session_management(self):
        """Configure unified session management"""
        
        self.platform.configure_sessions(
            session_store="redis",  # Requires Redis from INFRA-004
            session_timeout=3600,   # 1 hour
            cross_channel_sync=True,
            persistent_workflows=True
        )
    
    def _health_check(self):
        """Platform health check endpoint"""
        return {
            "status": "healthy",
            "services": {
                "api": self.platform.api_status(),
                "cli": self.platform.cli_status(), 
                "mcp": self.platform.mcp_status(),
                "websocket": self.platform.websocket_status()
            },
            "workflows": self.platform.get_available_workflows(),
            "sessions": self.platform.get_active_sessions_count()
        }
    
    async def _handle_classification_stream(self, websocket, path):
        """Handle real-time classification progress"""
        async for message in websocket:
            # Process classification request
            # Stream progress updates back to client
            pass
    
    async def _handle_recommendation_stream(self, websocket, path):
        """Handle streaming recommendation results"""
        async for message in websocket:
            # Process recommendation request
            # Stream results as they become available
            pass
    
    async def _handle_chat_stream(self, websocket, path):
        """Handle real-time chat with AI assistant"""
        async for message in websocket:
            # Process chat message
            # Stream AI response chunks
            pass
```

### Phase 3B-2: Multi-Channel Integration Testing (Hours 4-6)
```python
# test_multi_channel_integration.py
import pytest
import asyncio
import requests
import websockets
from nexus_platform_config import MultiChannelPlatformSetup

class TestMultiChannelIntegration:
    """Test suite for multi-channel platform functionality"""
    
    @pytest.fixture
    def platform_setup(self):
        """Setup Nexus platform for testing"""
        setup = MultiChannelPlatformSetup()
        platform = setup.setup_platform()
        platform.start()
        yield platform
        platform.stop()
    
    def test_api_endpoint_accessibility(self, platform_setup):
        """Test REST API endpoints are accessible"""
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # Test classification endpoint
        classification_data = {
            "product_description": "Cordless drill with lithium battery",
            "standards": ["UNSPSC", "ETIM"]
        }
        response = requests.post(
            "http://localhost:8000/api/v1/classify",
            json=classification_data
        )
        assert response.status_code == 200
        assert "classifications" in response.json()
    
    def test_cli_interface_functionality(self, platform_setup):
        """Test CLI interface can execute workflows"""
        
        import subprocess
        
        # Test classification command
        result = subprocess.run([
            "nexus", "classify", 
            "--input", "Cordless drill with lithium battery",
            "--format", "json"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert '"classifications"' in result.stdout
        
        # Test recommendation command
        result = subprocess.run([
            "nexus", "recommend",
            "--project-type", "kitchen renovation", 
            "--budget", "500-1000"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert '"recommendations"' in result.stdout
    
    async def test_mcp_server_integration(self, platform_setup):
        """Test MCP server functionality"""
        
        # Test MCP tool availability
        tools_response = requests.get("http://localhost:8001/mcp/tools")
        assert tools_response.status_code == 200
        
        tools = tools_response.json()["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        assert "classify_product" in tool_names
        assert "recommend_tools" in tool_names
        assert "search_products" in tool_names
        
        # Test MCP tool execution
        classification_request = {
            "tool": "classify_product",
            "parameters": {
                "product_description": "Cordless drill with lithium battery",
                "classification_standards": ["UNSPSC", "ETIM"]
            }
        }
        
        response = requests.post(
            "http://localhost:8001/mcp/execute",
            json=classification_request
        )
        
        assert response.status_code == 200
        assert "result" in response.json()
    
    async def test_websocket_connectivity(self, platform_setup):
        """Test WebSocket endpoints for real-time features"""
        
        # Test classification WebSocket
        async with websockets.connect("ws://localhost:8000/ws/classify") as websocket:
            
            # Send classification request
            await websocket.send(json.dumps({
                "product_description": "Cordless drill with lithium battery"
            }))
            
            # Receive progress updates
            response = await websocket.recv()
            data = json.loads(response)
            
            assert "progress" in data or "result" in data
        
        # Test chat WebSocket
        async with websockets.connect("ws://localhost:8000/ws/chat") as websocket:
            
            # Send chat message
            await websocket.send(json.dumps({
                "message": "I need recommendations for a kitchen renovation project"
            }))
            
            # Receive AI response
            response = await websocket.recv()
            data = json.loads(response)
            
            assert "response" in data
    
    def test_unified_session_management(self, platform_setup):
        """Test session persistence across channels"""
        
        # Create session via API
        api_session = requests.post("http://localhost:8000/api/v1/session/create")
        session_id = api_session.json()["session_id"]
        
        # Use same session in CLI
        result = subprocess.run([
            "nexus", "classify",
            "--session", session_id,
            "--input", "Test product"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        
        # Verify session state via MCP
        mcp_session = requests.get(
            f"http://localhost:8001/mcp/session/{session_id}"
        )
        assert mcp_session.status_code == 200
        assert mcp_session.json()["active"] is True
    
    def test_cross_channel_workflow_consistency(self, platform_setup):
        """Test workflow execution consistency across channels"""
        
        test_input = {
            "product_description": "Cordless drill with lithium battery",
            "standards": ["UNSPSC", "ETIM"]
        }
        
        # Execute via API
        api_response = requests.post(
            "http://localhost:8000/api/v1/classify",
            json=test_input
        ).json()
        
        # Execute via CLI
        cli_result = subprocess.run([
            "nexus", "classify",
            "--input", test_input["product_description"],
            "--standards", "both",
            "--format", "json"
        ], capture_output=True, text=True)
        
        cli_response = json.loads(cli_result.stdout)
        
        # Execute via MCP
        mcp_response = requests.post(
            "http://localhost:8001/mcp/execute",
            json={
                "tool": "classify_product",
                "parameters": test_input
            }
        ).json()["result"]
        
        # Verify consistent results
        assert api_response["classifications"] == cli_response["classifications"]
        assert api_response["classifications"] == mcp_response["classifications"]
```

## Testing Requirements

### Unit Tests (Critical Priority)
- [ ] Nexus platform initialization and configuration
- [ ] Multi-channel endpoint registration and routing
- [ ] Session management and cross-channel synchronization
- [ ] Workflow execution consistency across interfaces

### Integration Tests (High Priority)
- [ ] API endpoint functionality with real workflow execution
- [ ] CLI interface complete workflow testing
- [ ] MCP server tool registration and execution
- [ ] WebSocket real-time communication testing

### End-to-End Tests (Medium Priority)
- [ ] Complete user workflows across all three channels
- [ ] Session persistence and state management validation
- [ ] Performance testing under concurrent multi-channel load
- [ ] Error handling and recovery across all interfaces

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] Nexus platform deployed with API + CLI + MCP server simultaneously
- [ ] Unified session management working across all interfaces
- [ ] Workflow execution consistent and reliable across all channels
- [ ] Real-time WebSocket endpoints operational
- [ ] Comprehensive testing suite passing for all multi-channel functionality
- [ ] Documentation updated with deployment and usage instructions
- [ ] Performance validated under expected load conditions

## Implementation Files

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\nexus_platform_config.py` (new)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\tests\integration\test_multi_channel_integration.py` (new)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\docker-compose.nexus.yml` (new)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\docs\nexus-deployment-guide.md` (new)

## Progress Tracking

**Phase 3B-1 (Hours 1-3):** [ ] Nexus core platform setup and configuration  
**Phase 3B-2 (Hours 4-6):** [ ] API, CLI, and MCP interface implementation  
**Phase 3B-3 (Hours 7-9):** [ ] WebSocket and real-time feature integration  
**Phase 3B-4 (Hours 10-11):** [ ] Unified session management and testing  
**Phase 3B-5 (Hour 12):** [ ] Multi-channel validation and documentation  

## Success Metrics

- **Multi-Channel Availability**: 100% uptime across API, CLI, and MCP interfaces
- **Session Consistency**: 100% session sync accuracy across all channels
- **Workflow Performance**: <2s response time for all workflow executions
- **Concurrent User Support**: Handle 100+ simultaneous sessions across channels
- **Error Rate**: <0.1% error rate across all interface methods

## Next Actions After Completion

1. **AI-001**: Custom Classification Workflows (depends on Nexus platform deployment)
2. **FE-001**: Next.js API Client Setup (uses Nexus API endpoints)
3. **FE-005**: WebSocket Client Integration (connects to Nexus WebSocket handlers)

This multi-channel platform provides the unified foundation for all subsequent frontend and AI integration work.