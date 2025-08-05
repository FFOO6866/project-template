# Production MCP Server for AI Agent Support

A comprehensive, production-ready MCP (Model Context Protocol) server implementation that provides advanced AI agent support with dynamic tool discovery, authentication, performance optimization, and comprehensive monitoring.

## 🚀 Key Features

### Core Capabilities
- **117 DataFlow Tools**: All DataFlow nodes automatically registered as MCP tools
- **Dynamic Tool Discovery**: Real-time tool registration and capability detection
- **Multi-Transport Support**: STDIO, HTTP, and WebSocket transports
- **Production Authentication**: JWT, API Key, and Bearer token authentication
- **Agent Coordination**: Advanced session management and multi-agent collaboration
- **Performance Optimization**: Circuit breakers, rate limiting, and caching
- **Real-time Monitoring**: Comprehensive metrics and analytics
- **Error Handling**: Structured error responses with retry strategies

### Enterprise Features
- **Concurrent Request Handling**: Support for 500+ concurrent requests
- **Connection Pooling**: Optimized database connection management
- **Circuit Breaker Pattern**: Automatic failure detection and recovery
- **Rate Limiting**: Per-agent and global rate limiting
- **Intelligent Caching**: TTL-based caching with compression
- **Session Management**: Persistent agent sessions with collaboration
- **Workflow Orchestration**: Multi-step workflow execution and caching
- **Health Monitoring**: Comprehensive health checks and status reporting

## 📁 File Structure

```
src/new_project/
├── production_mcp_server.py              # Main production MCP server
├── enhanced_nexus_mcp_integration.py     # Nexus platform integration
├── mcp_agent_integration_demo.py         # Demo and testing script
├── start_production_mcp_server.py        # Startup script with CLI
├── mcp_server_config.json               # Configuration file
└── PRODUCTION_MCP_SERVER_GUIDE.md       # This documentation
```

## 🛠️ Installation and Setup

### Prerequisites

```bash
# Core dependencies
pip install kailash[mcp]  # MCP SDK support
pip install fastapi uvicorn  # HTTP transport
pip install PyJWT  # JWT authentication
pip install psutil  # Performance monitoring

# DataFlow integration (if available)
pip install kailash[dataflow]

# Optional: Enhanced features
pip install redis  # Redis caching
pip install prometheus-client  # Metrics export
```

### Quick Start

#### 1. Standalone Server

```bash
# Start with default configuration
python start_production_mcp_server.py --mode standalone

# Start with custom port and JWT auth
python start_production_mcp_server.py --mode standalone --port 3001 --auth-type jwt

# Start with configuration file
python start_production_mcp_server.py --config mcp_server_config.json
```

#### 2. Nexus Integration

```bash
# Integrate with existing Nexus platform
python start_production_mcp_server.py --mode nexus-integration
```

#### 3. Development Mode

```bash
# Development mode with mock DataFlow
python start_production_mcp_server.py --mode development --no-auth
```

### Configuration

Edit `mcp_server_config.json` to customize server behavior:

```json
{
  "port": 3001,
  "host": "0.0.0.0",
  "enable_auth": true,
  "auth_type": "jwt",
  "jwt_secret": "your-secret-key",
  "max_concurrent_requests": 500,
  "request_timeout_seconds": 60,
  "rate_limit_per_minute": 1000,
  "enable_caching": true,
  "cache_ttl_seconds": 1800,
  "enable_agent_collaboration": true,
  "enable_performance_tracking": true,
  "enable_http_transport": true
}
```

## 🔧 Usage Examples

### 1. Basic AI Agent Integration

```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# MCP server configuration
mcp_config = {
    "name": "production-dataflow-server",
    "transport": "stdio",
    "command": "python",
    "args": ["-m", "production_mcp_server"],
    "auth": {"type": "api_key", "key": "agent_key"}
}

# Create AI agent workflow with MCP integration
workflow = WorkflowBuilder()

workflow.add_node("LLMAgentNode", "ai_agent", {
    "provider": "openai",
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": "You are an AI agent with access to DataFlow operations."},
        {"role": "user", "content": "Create a new company and list all companies."}
    ],
    "mcp_servers": [mcp_config],
    "auto_discover_tools": True,
    "auto_execute_tools": True,
    "tools_to_use": ["Company_create", "Company_list"]
})

runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
```

### 2. Agent Session Management

```python
import asyncio
from production_mcp_server import ProductionMCPServer, ServerConfig

# Create server
config = ServerConfig(enable_agent_collaboration=True)
server = ProductionMCPServer(config)

# Start server in background
server.start_mcp_server_async()

# Create agent session (via MCP tool)
session_result = await server.mcp_server.call_tool(
    "create_agent_session",
    {
        "agent_id": "my_ai_agent", 
        "agent_info": {
            "type": "llm_agent",
            "model": "gpt-4",
            "capabilities": ["dataflow_operations", "analysis"]
        }
    }
)

session_id = session_result["session_id"]
print(f"Created session: {session_id}")
```

### 3. Multi-Step Workflow Orchestration

```python
# Create workflow session
workflow_session = await server.mcp_server.call_tool(
    "create_agent_workflow_session",
    {
        "agent_id": "workflow_agent",
        "workflow_type": "customer_onboarding",
        "session_config": {"enable_caching": True}
    }
)

workflow_session_id = workflow_session["workflow_session_id"]

# Execute workflow steps
steps = [
    {
        "step_name": "create_customer",
        "type": "dataflow_operation",
        "model": "Customer",
        "operation": "create",
        "parameters": {
            "data": {
                "name": "Acme Corp",
                "email": "contact@acme.com",
                "industry": "technology"
            }
        }
    },
    {
        "step_name": "create_quote",
        "type": "dataflow_operation", 
        "model": "Quote",
        "operation": "create",
        "parameters": {
            "data": {
                "customer_id": "{{previous_result.id}}",
                "total_amount": 10000.00,
                "status": "draft"
            }
        }
    }
]

for step in steps:
    result = await server.mcp_server.call_tool(
        "execute_workflow_step",
        {
            "workflow_session_id": workflow_session_id,
            "step_name": step["step_name"],
            "step_config": step
        }
    )
    print(f"Step {step['step_name']}: {result['success']}")
```

### 4. HTTP API Usage

```bash
# List available tools
curl http://localhost:3002/tools

# Execute DataFlow operation
curl -X POST http://localhost:3002/tools/Company_create \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "TechFlow Inc",
      "industry": "technology",
      "is_active": true
    },
    "_agent_id": "api_agent",
    "_session_id": "session123"
  }'

# Get server metrics
curl http://localhost:3002/metrics
```

### 5. Nexus Platform Integration

```python
from enhanced_nexus_mcp_integration import enhance_nexus_with_mcp
from nexus_dataflow_platform import app as nexus_app

# Enhance existing Nexus app with production MCP
integration = enhance_nexus_with_mcp(nexus_app)

# Access enhanced endpoints
# GET /api/mcp/status - MCP server status
# POST /api/mcp/execute-tool - Execute MCP tools via HTTP
# GET /api/mcp/tools - List all available tools
```

## 🧪 Testing and Validation

### Run Integration Demo

```bash
# Start the MCP server first
python start_production_mcp_server.py --mode development &

# Run comprehensive integration demo
python mcp_agent_integration_demo.py
```

The demo includes:
- Agent session creation and management
- Dynamic tool discovery
- DataFlow operations execution
- Multi-agent collaboration
- Performance monitoring
- Complex workflow orchestration
- Health check validation

### Monitoring and Metrics

The server provides comprehensive metrics:

```python
# Get server metrics via MCP tool
metrics = await server.mcp_server.call_tool("get_server_metrics")

print(f"Total requests: {metrics['server_metrics']['total_requests']}")
print(f"Average response time: {metrics['server_metrics']['average_response_time_ms']}ms")
print(f"Error rate: {metrics['server_metrics']['error_rate_percent']}%")
print(f"Active sessions: {metrics['session_analytics']['active_sessions']}")
print(f"Cache hit ratio: {metrics['server_metrics']['cache_hit_ratio']}")
```

### Health Checks

```python
# Comprehensive health check
health = await server.mcp_server.call_tool("health_check")

print(f"Overall status: {health['health_status']}")
for component, info in health['components'].items():
    print(f"{component}: {info['status']}")
```

## 🏗️ Architecture Overview

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Clients                         │
│  (LLMAgentNode, Custom Agents, External AI Systems)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Transport Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │    STDIO    │ │    HTTP     │ │      WebSocket          │ │
│  │  (Default)  │ │  (Port+1)   │ │    (Future)             │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Production MCP Server                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Authentication Layer                       │ │
│  │        (JWT, API Key, Bearer Token)                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Agent Session Management                      │ │
│  │   (Sessions, Collaboration, Performance Tracking)      │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Tool Discovery Engine                      │ │
│  │        (Dynamic Registration, Metadata)                │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Performance Optimization                     │ │
│  │   (Circuit Breakers, Rate Limiting, Caching)          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                DataFlow Integration                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              117 Auto-Generated Tools                  │ │
│  │  Company(9) + User(9) + Customer(9) + Quote(9) +      │ │
│  │  ProductClassification(9) + ... + Document(9)          │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Workflow Orchestration                       │ │
│  │        (Multi-step, Caching, Error Recovery)           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Database & Storage Layer                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │        PostgreSQL (Production) / SQLite (Dev)           │ │
│  │           Connection Pooling & Optimization             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Agent Request**: AI agent sends MCP request via transport
2. **Authentication**: Request authenticated and authorized
3. **Session Management**: Agent session created/validated
4. **Tool Discovery**: Available tools discovered dynamically
5. **Request Processing**: Tool executed with performance monitoring
6. **DataFlow Operation**: Database operation via optimized workflow
7. **Response Formatting**: Structured response with metadata
8. **Caching**: Results cached for future requests
9. **Metrics Collection**: Performance metrics recorded
10. **Response Delivery**: Response sent back to agent

## 🔧 Available Tools

### DataFlow Tools (117 Total)

Each DataFlow model provides 9 operations:

#### Company Tools (9)
- `Company_create` - Create new company
- `Company_read` - Read company by ID
- `Company_update` - Update company data
- `Company_delete` - Delete company
- `Company_list` - List companies with filtering
- `Company_bulk_create` - Bulk create companies
- `Company_bulk_update` - Bulk update companies
- `Company_bulk_delete` - Bulk delete companies
- `Company_bulk_upsert` - Bulk insert/update companies

#### User Tools (9)
- `User_create`, `User_read`, `User_update`, `User_delete`, `User_list`
- `User_bulk_create`, `User_bulk_update`, `User_bulk_delete`, `User_bulk_upsert`

#### Customer Tools (9)
- `Customer_create`, `Customer_read`, `Customer_update`, `Customer_delete`, `Customer_list`
- `Customer_bulk_create`, `Customer_bulk_update`, `Customer_bulk_delete`, `Customer_bulk_upsert`

#### Quote Tools (9)
- `Quote_create`, `Quote_read`, `Quote_update`, `Quote_delete`, `Quote_list`
- `Quote_bulk_create`, `Quote_bulk_update`, `Quote_bulk_delete`, `Quote_bulk_upsert`

#### AI Classification Tools (45 total)
- **ProductClassification** (9 tools) - AI-powered product classification
- **ClassificationHistory** (9 tools) - Classification audit trail
- **ClassificationCache** (9 tools) - Performance optimization cache
- **ClassificationRule** (9 tools) - Business classification rules
- **ClassificationFeedback** (9 tools) - ML feedback loop

#### Standards Integration Tools (9)
- **ETIMAttribute** (9 tools) - ETIM standard attributes

#### Analytics Tools (9)
- **ClassificationMetrics** (9 tools) - Performance analytics

#### Document Management Tools (18)
- **Document** (9 tools) - Document management
- **DocumentProcessingQueue** (9 tools) - Document processing pipeline

### Utility Tools

#### Session Management
- `create_agent_session` - Create persistent agent session
- `enable_agent_collaboration` - Enable multi-agent collaboration

#### Tool Discovery
- `get_available_tools` - Get all available tools with metadata
- `get_dataflow_models_info` - Get detailed DataFlow model information

#### Monitoring
- `get_server_metrics` - Get comprehensive server metrics
- `health_check` - Comprehensive server health check

#### Workflow Orchestration
- `create_agent_workflow_session` - Create workflow session
- `execute_workflow_step` - Execute single workflow step
- `get_workflow_session_status` - Get workflow session status

#### Nexus Integration
- `execute_nexus_workflow` - Execute registered Nexus workflow
- `get_nexus_workflows` - Get available Nexus workflows

#### Integration Analytics
- `get_integration_metrics` - Get Nexus-MCP integration metrics
- `cleanup_workflow_sessions` - Clean up inactive sessions

## 🚨 Production Deployment

### Security Configuration

```json
{
  "enable_auth": true,
  "auth_type": "jwt",
  "jwt_secret": "CHANGE-THIS-IN-PRODUCTION",
  "jwt_expiration_hours": 24,
  "rate_limit_per_minute": 1000,
  "circuit_breaker_failure_threshold": 10,
  "enable_performance_tracking": true
}
```

### Performance Tuning

```json
{
  "max_concurrent_requests": 500,
  "connection_pool_size": 20,
  "connection_pool_max_overflow": 40,
  "connection_recycle_seconds": 1800,
  "cache_ttl_seconds": 1800,
  "cache_max_size_mb": 256,
  "request_timeout_seconds": 60
}
```

### Monitoring Setup

```json
{
  "enable_metrics": true,
  "metrics_collection_interval": 30,
  "enable_agent_analytics": true,
  "agent_session_timeout_minutes": 30
}
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/production

# Authentication
JWT_SECRET=your-production-secret-key
API_KEYS='{"admin_key": {"permissions": ["*"], "rate_limit": 10000}}'

# Performance
MCP_MAX_CONCURRENT_REQUESTS=500
MCP_CACHE_TTL_SECONDS=1800
MCP_ENABLE_COMPRESSION=true

# Monitoring
MCP_ENABLE_METRICS=true
MCP_LOG_LEVEL=INFO
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY src/new_project/ .

# Set environment
ENV PYTHONPATH=/app
ENV MCP_CONFIG_FILE=mcp_server_config.json

# Expose ports
EXPOSE 3001 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:3002/health')"

# Start server
CMD ["python", "start_production_mcp_server.py", "--mode", "standalone"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "3001:3001"  # MCP STDIO
      - "3002:3002"  # HTTP API
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mcp_production
      - JWT_SECRET=production-secret-key
      - MCP_ENABLE_METRICS=true
    volumes:
      - ./mcp_server_config.json:/app/mcp_server_config.json
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_production
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "DataFlow models not available"

**Solution**: Install DataFlow or run in development mode
```bash
pip install kailash[dataflow]
# OR
python start_production_mcp_server.py --mode development
```

#### 2. "JWT support not available"

**Solution**: Install PyJWT
```bash
pip install PyJWT
```

#### 3. "Tool {tool_name} not found"

**Cause**: Tool discovery failed or tool name incorrect

**Solution**: Check available tools
```python
tools = await server.mcp_server.call_tool("get_available_tools")
print([tool['name'] for tool in tools['tools']])
```

#### 4. "Circuit breaker open for tool {tool_name}"

**Cause**: Tool experiencing repeated failures

**Solution**: Check tool health and wait for recovery
```python
health = await server.mcp_server.call_tool("health_check")
print(health['components'])
```

#### 5. "Rate limit exceeded"

**Cause**: Too many requests from agent

**Solution**: Increase rate limit or implement request throttling
```json
{
  "rate_limit_per_minute": 2000
}
```

### Debug Mode

```bash
# Enable debug logging
python start_production_mcp_server.py --log-level DEBUG

# Check server logs
tail -f production_mcp_server.log
```

### Performance Analysis

```python
# Get detailed performance metrics
metrics = await server.mcp_server.call_tool("get_server_metrics")

# Check slow requests
if metrics['server_metrics']['slow_request_ratio'] > 0.1:
    print("High ratio of slow requests detected")
    print(f"Slow requests: {metrics['server_metrics']['slow_requests']}")

# Check memory usage
if metrics['server_metrics']['memory_usage_mb'] > 1000:
    print("High memory usage detected")
    # Consider cleanup or restart
```

## 📚 API Reference

For complete API documentation, see the inline documentation in:
- `production_mcp_server.py` - Core server implementation
- `enhanced_nexus_mcp_integration.py` - Nexus integration features
- `mcp_agent_integration_demo.py` - Usage examples and patterns

## 🤝 Contributing

The production MCP server is designed to be extensible. Key extension points:

1. **Custom Authentication Providers**: Extend `AuthProvider` class
2. **Additional Tool Categories**: Add to `DataFlowToolDiscovery`
3. **Custom Transport Layers**: Implement `BaseTransport`
4. **Monitoring Integrations**: Extend `ServerMetrics` class
5. **Workflow Orchestration**: Add custom workflow patterns

## 📄 License

This production MCP server implementation is part of the Kailash SDK ecosystem and follows the same licensing terms.

---

**Ready for production AI agent workloads with enterprise-grade reliability, performance, and monitoring.**
