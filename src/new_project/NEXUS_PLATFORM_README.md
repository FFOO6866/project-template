# Nexus DataFlow Multi-Channel Platform

## 🚀 Overview

Production-ready **Nexus multi-channel platform** providing unified **API + CLI + MCP** access to a complete **DataFlow foundation** with 13 models and 117 auto-generated database nodes.

### 🎯 Key Features

- **Multi-Channel Deployment**: Simultaneous API, CLI, and MCP server access
- **DataFlow Integration**: Complete access to 117 auto-generated database operation nodes
- **Zero-Configuration**: Intelligent defaults with production-ready configuration
- **Performance Optimized**: <2s response time targets with intelligent caching
- **Enterprise Ready**: Authentication, monitoring, rate limiting, and scalability
- **Windows Compatible**: Native Windows support with batch scripts

### 📊 DataFlow Foundation

**13 Business Models** → **117 Auto-Generated Nodes**:

| Model | Operations | Use Case |
|-------|-----------|----------|
| **Company** | 9 nodes | Business entity management |
| **User** | 9 nodes | Authentication and profiles |
| **Customer** | 9 nodes | Client relationship management |
| **Quote** | 9 nodes | Sales quotation workflow |
| **ProductClassification** | 9 nodes | AI-powered product classification |
| **ClassificationHistory** | 9 nodes | Audit trail and change tracking |
| **ClassificationCache** | 9 nodes | Performance optimization |
| **ETIMAttribute** | 9 nodes | Technical specifications |
| **ClassificationRule** | 9 nodes | ML training and rules |
| **ClassificationFeedback** | 9 nodes | Continuous learning |
| **ClassificationMetrics** | 9 nodes | Performance monitoring |
| **Document** | 9 nodes | Document management |
| **DocumentProcessingQueue** | 9 nodes | AI workflow processing |

**Each model automatically generates**: Create, Read, Update, Delete, List, BulkCreate, BulkUpdate, BulkDelete, BulkUpsert

## 🛠️ Quick Start

### Windows Installation

1. **Clone and Navigate**:
   ```bash
   cd src/new_project
   ```

2. **Install Dependencies**:
   ```bash
   pip install nexus kailash dataflow fastapi uvicorn pyjwt psycopg2-binary
   ```

3. **Start Platform** (Easy Way):
   ```bash
   start_nexus.bat
   ```

4. **Or Start with Python**:
   ```bash
   python start_nexus_platform.py
   ```

5. **Verify Installation**:
   ```bash
   python test_nexus_platform.py --quick
   ```

### Access Points

Once started, the platform provides multi-channel access:

- **REST API**: http://localhost:8000
  - Interactive docs: http://localhost:8000/docs
  - Health check: http://localhost:8000/api/health
- **CLI**: `nexus --help`
- **MCP Server**: http://localhost:3001

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 Nexus Platform                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   API    │  │   CLI    │  │   MCP    │     │
│  │ Channel  │  │ Channel  │  │ Channel  │     │
│  │ :8000    │  │  nexus   │  │ :3001    │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       └──────────────┴──────────────┘           │
│         Unified Session & Authentication        │
│  ┌─────────────────────────────────────────────┐ │
│  │          DataFlow Engine                    │ │
│  │   13 Models → 117 Auto-Generated Nodes     │ │
│  └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│            Database Layer                       │
│  PostgreSQL (Production) / SQLite (Development) │
└─────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables

```bash
# Server Configuration
NEXUS_ENV=development                # development/production
NEXUS_API_PORT=8000                 # API server port
NEXUS_MCP_PORT=3001                 # MCP server port
NEXUS_API_HOST=0.0.0.0              # API host binding

# Security
NEXUS_JWT_SECRET=your-secret-key     # JWT signing secret

# Database (Production)
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### Configuration File

The platform automatically creates `nexus_config.json`:

```json
{
  "environment": "development",
  "server": {
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "mcp_port": 3001,
    "enable_compression": true
  },
  "security": {
    "jwt_expiration_hours": 24,
    "enable_cors": true,
    "cors_origins": ["http://localhost:3000"]
  },
  "performance": {
    "cache_ttl_seconds": 300,
    "max_concurrent_requests": 100,
    "request_timeout": 30
  }
}
```

## 📡 API Usage

### DataFlow Operations

**Unified endpoint for all 117 auto-generated nodes**:

```bash
# Create company
POST /api/dataflow/company/create
{
  "name": "Acme Corp",
  "industry": "technology",
  "is_active": true
}

# List users with filtering
POST /api/dataflow/user/list
{
  "filters": {"is_active": true},
  "limit": 50,
  "offset": 0
}

# Bulk create customers
POST /api/dataflow/customer/bulk_create
{
  "data": [
    {"name": "Customer 1", "email": "customer1@example.com"},
    {"name": "Customer 2", "email": "customer2@example.com"}
  ]
}
```

### Classification Workflows

**AI-powered product classification**:

```bash
POST /api/classification/classify
{
  "product_data": {
    "name": "Industrial Pump",
    "description": "Centrifugal pump for industrial applications",
    "category": "machinery"
  },
  "classification_method": "ml_automatic",
  "confidence_threshold": 0.7
}
```

### Bulk Operations

**High-performance bulk processing**:

```bash
POST /api/bulk/create
{
  "model": "product_classification",
  "data": [...],  # Array of records
  "batch_size": 1000
}
```

## 🖥️ CLI Usage

```bash
# Show DataFlow status
nexus dataflow-status

# Performance monitoring
nexus performance-report

# Cache management
nexus cache-stats
nexus clear-cache --pattern "user_*"

# Workflow patterns
nexus workflow-patterns

# Health monitoring
nexus health-check
```

## 🤖 MCP Integration

The platform automatically exposes **MCP tools** for AI agents:

```python
# Available MCP tools
tools = [
    "dataflow_operation",      # Access any of the 117 DataFlow nodes
    "classify_product",        # AI product classification
    "bulk_operation",          # High-performance bulk processing
    "get_system_health",       # Platform monitoring
]

# Example: AI agent classifying products
result = mcp_client.call_tool("classify_product", {
    "product_data": {
        "name": "Electric Motor",
        "description": "3-phase induction motor, 5HP"
    },
    "classification_method": "ml_automatic"
})
```

## 🚀 Performance Optimization

### Caching Strategy

- **Read Operations**: Automatic caching with 5-minute TTL
- **User Sessions**: JWT with intelligent refresh
- **Classification Results**: Intelligent cache warming
- **Dashboard Data**: Real-time updates with caching

### Performance Targets

- **API Response Time**: <2000ms (typical <500ms)
- **Classification**: <800ms including cache lookup
- **Bulk Operations**: 10,000+ records/second
- **Dashboard Updates**: <200ms with caching

### Monitoring

```bash
# Check performance metrics
GET /api/metrics

# Health monitoring
GET /api/health

# Real-time dashboard
GET /api/dashboard
```

## 🧪 Testing

### Quick Test

```bash
python test_nexus_platform.py --quick
```

### Full Test Suite

```bash
python test_nexus_platform.py
```

**Test Coverage**:
- ✅ Health checks and monitoring
- ✅ API endpoint functionality
- ✅ DataFlow integration
- ✅ Authentication and security
- ✅ Performance benchmarks
- ✅ CLI interface
- ✅ Error handling
- ✅ Configuration management

## 🔐 Security

### Authentication

- **JWT Tokens**: Secure session management
- **Session Validation**: Real-time session checking
- **Role-Based Access**: User roles and permissions
- **CORS Protection**: Configurable origin control

### Security Headers

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## 📈 Monitoring & Analytics

### Built-in Monitoring

- **Request Metrics**: Response times, error rates
- **Cache Performance**: Hit ratios, efficiency
- **DataFlow Operations**: Database performance
- **WebSocket Connections**: Real-time monitoring

### Health Checks

```json
{
  "status": "healthy",
  "dataflow": {
    "status": "healthy",
    "models_count": 13,
    "nodes_count": 117
  },
  "performance": {
    "average_response_time_ms": 245,
    "cache_hit_ratio": 0.85,
    "error_rate": 0.001
  }
}
```

## 🚀 Production Deployment

### PostgreSQL Setup

1. **Install PostgreSQL** with extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "pgvector";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";
   CREATE EXTENSION IF NOT EXISTS "btree_gin";
   ```

2. **Configure Database**:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/horme_classification_db
   ```

3. **Update Configuration**:
   ```json
   {
     "environment": "production",
     "database": {
       "type": "postgresql",
       "pool_size": 30,
       "pool_max_overflow": 60
     }
   }
   ```

### Production Optimizations

- **Connection Pooling**: 30 base connections, 60 overflow
- **Cache Backend**: Redis for distributed caching
- **Load Balancing**: Multiple Nexus instances
- **Monitoring**: Prometheus metrics integration

## 🔧 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Check dependencies
python start_nexus_platform.py check

# Install missing packages
pip install -r requirements.txt
```

**2. Database Connection**
```bash
# For development, SQLite is used automatically
# For production, ensure PostgreSQL is running
```

**3. Port Conflicts**
```bash
# Change ports in environment variables
NEXUS_API_PORT=8001
NEXUS_MCP_PORT=3002
```

**4. Performance Issues**
```bash
# Check cache statistics
nexus cache-stats

# Clear cache if needed
nexus clear-cache
```

### Logging

Logs are written to console with structured format:
```
2024-01-01 12:00:00 - nexus_dataflow_platform - INFO - Platform ready
```

## 📚 API Reference

### DataFlow Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dataflow/{model}/{operation}` | POST | Execute any DataFlow operation |
| `/api/classification/classify` | POST | AI product classification |
| `/api/bulk/{operation}` | POST | Bulk data operations |
| `/api/dashboard` | GET | Analytics dashboard |
| `/api/health` | GET | Platform health check |
| `/api/metrics` | GET | Performance metrics |

### Response Format

```json
{
  "success": true,
  "data": {...},
  "metadata": {
    "execution_time_ms": 245,
    "cached": false,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## 🤝 Contributing

1. **DataFlow Models**: Add new models in `dataflow_classification_models.py`
2. **Workflows**: Create workflows in `nexus_dataflow_platform.py`
3. **Tests**: Add tests in `test_nexus_platform.py`
4. **Documentation**: Update this README

## 📄 License

This project is part of the Kailash SDK ecosystem. See main repository for license information.

---

## 🎉 Success Metrics

**Platform Ready Indicators**:
- ✅ All 13 DataFlow models loaded
- ✅ 117 auto-generated nodes available
- ✅ Multi-channel access (API + CLI + MCP)
- ✅ <2s response time target met
- ✅ Health checks passing
- ✅ Authentication working
- ✅ Caching operational

**Ready for**:
- 🎯 Production deployment
- 🤖 AI agent integration
- 📊 Real-time analytics
- 🚀 Enterprise scaling