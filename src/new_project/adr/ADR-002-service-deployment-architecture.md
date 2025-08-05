# ADR-002: Service Deployment Architecture Requirements

**Status:** Proposed  
**Date:** 2025-08-03  
**Authors:** Requirements Analysis Specialist  
**Reviewers:** Framework Advisor, Nexus Specialist, Infrastructure Team  
**Related ADRs:** ADR-001 (Windows Development Environment Strategy)

---

## Context

The Kailash SDK multi-framework implementation requires a comprehensive service deployment architecture to support Core SDK, DataFlow, and Nexus platform integration. The system must handle:

### Technical Requirements
- **Multi-Framework Coordination**: Core SDK workflows + DataFlow auto-generation + Nexus multi-channel platform
- **Service Dependencies**: PostgreSQL, Neo4j, ChromaDB, Redis with real connections (NO MOCKING)
- **Performance Targets**: <500ms classification, <2s recommendations, 100+ concurrent users
- **Platform Support**: Windows development with WSL2+Docker, Linux production deployment

### Business Requirements
- **Classification System**: 170,000+ UNSPSC codes, 49,000+ ETIM classes, >95% accuracy
- **Safety Compliance**: OSHA/ANSI rule engine with automated checking
- **Multi-Channel Access**: Simultaneous API + CLI + MCP deployment
- **Real-time Features**: WebSocket streaming, progressive UI updates

### Constraints
- **Windows Development**: Must work in WSL2+Docker hybrid environment
- **Production Readiness**: Zero-downtime deployments, 99.9% uptime SLA
- **Security Requirements**: SOC 2 Type II compliance, GDPR ready
- **Scalability**: Horizontal scaling for 1000+ requests/second

---

## Decision

**Adopt Containerized Microservices Architecture with Kubernetes Orchestration**

### Primary Architecture Components

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[NGINX Ingress Controller]
        SSL[SSL Termination]
    end
    
    subgraph "Application Layer"
        API[Nexus API Service]
        CLI[CLI Service]
        MCP[MCP Server]
        WS[WebSocket Service]
        WORKER[Background Workers]
    end
    
    subgraph "Framework Layer"
        CORE[Core SDK Runtime]
        DF[DataFlow Engine]
        NX[Nexus Platform]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        NEO[(Neo4j)]
        CHROMA[(ChromaDB)]
        REDIS[(Redis)]
    end
    
    subgraph "AI Services"
        OPENAI[OpenAI API]
        ML[ML Models]
        EMB[Embedding Service]
    end
    
    LB --> API
    LB --> WS
    API --> CORE
    API --> DF
    API --> NX
    CORE --> PG
    DF --> PG
    NX --> REDIS
    API --> NEO
    API --> CHROMA
    WORKER --> OPENAI
    WORKER --> ML
```

### Service Architecture Design

#### Core Application Services
```yaml
nexus-api:
  image: kailash/nexus-api:latest
  replicas: 3
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
  ports:
    - 8000:8000
  environment:
    - DATABASE_URL=postgresql://user:pass@postgres:5432/kailash
    - REDIS_URL=redis://redis:6379/0
    - NEO4J_URL=bolt://neo4j:7687
    - CHROMADB_URL=http://chromadb:8000

nexus-websocket:
  image: kailash/nexus-websocket:latest
  replicas: 2
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  ports:
    - 8001:8001

nexus-worker:
  image: kailash/nexus-worker:latest
  replicas: 5
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
  environment:
    - CELERY_BROKER=redis://redis:6379/1
    - OPENAI_API_KEY=${OPENAI_API_KEY}
```

#### Database Services Configuration
```yaml
postgresql:
  image: postgres:15-alpine
  replicas: 1
  resources:
    requests:
      memory: "4Gi"
      cpu: "2000m"
    limits:
      memory: "8Gi"
      cpu: "4000m"
  volumes:
    - postgres-data:/var/lib/postgresql/data
  environment:
    - POSTGRES_DB=kailash
    - POSTGRES_USER=kailash_user
    - POSTGRES_PASSWORD=${DB_PASSWORD}
  config:
    max_connections: 200
    shared_buffers: 1GB
    effective_cache_size: 4GB
    maintenance_work_mem: 256MB

neo4j:
  image: neo4j:5.3-community
  replicas: 1
  resources:
    requests:
      memory: "4Gi"
      cpu: "2000m"
    limits:
      memory: "8Gi"
      cpu: "4000m"
  volumes:
    - neo4j-data:/data
    - neo4j-logs:/logs
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    - NEO4J_dbms_memory_heap_initial__size=2g
    - NEO4J_dbms_memory_heap_max__size=4g
    - NEO4J_dbms_memory_pagecache_size=2g

chromadb:
  image: chromadb/chroma:latest
  replicas: 2
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
  volumes:
    - chromadb-data:/chroma/chroma
  environment:
    - CHROMA_SERVER_HOST=0.0.0.0
    - CHROMA_SERVER_HTTP_PORT=8000

redis:
  image: redis:7-alpine
  replicas: 1
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  volumes:
    - redis-data:/data
  config:
    maxmemory: 1gb
    maxmemory-policy: allkeys-lru
    save: "900 1 300 10 60 10000"
```

### Multi-Framework Integration Strategy

#### Core SDK Integration
- **Runtime Execution**: LocalRuntime with containerized execution environment
- **Node Registration**: @register_node decorator pattern across all services
- **Workflow Orchestration**: Centralized workflow execution with distributed node processing
- **Parameter Validation**: SecureGovernedNode pattern for all data processing nodes

#### DataFlow Framework Integration
- **Model Auto-Generation**: 13 business models → 117 auto-generated nodes
- **Database Connection**: Dedicated PostgreSQL connection pool for DataFlow operations
- **Transaction Management**: ACID compliance with distributed transaction coordination
- **Performance Optimization**: Connection pooling, query optimization, result caching

#### Nexus Platform Integration
- **Multi-Channel Deployment**: Simultaneous API + CLI + MCP server deployment
- **Session Management**: Unified sessions across all access channels with Redis backing
- **Authentication**: JWT-based authentication with refresh token rotation
- **Load Balancing**: Round-robin with health checks and failover

---

## Consequences

### Positive Outcomes

#### Scalability and Performance
- **Horizontal Scaling**: Independent scaling of application components based on load
- **Resource Optimization**: Dedicated resource allocation per service type
- **Performance Isolation**: Database bottlenecks don't affect API responsiveness
- **Cache Efficiency**: Multi-level caching with Redis and application-level caching

#### Reliability and Availability
- **High Availability**: Service redundancy with automatic failover
- **Health Monitoring**: Comprehensive health checks and automated recovery
- **Zero-Downtime Deployments**: Rolling updates with blue-green deployment strategy
- **Disaster Recovery**: Automated backup and restore procedures

#### Development and Operations
- **Environment Parity**: Identical configuration from development to production
- **Service Isolation**: Independent deployment and scaling of components
- **Monitoring Integration**: Comprehensive observability with Prometheus and Grafana
- **Configuration Management**: Environment-specific configuration with secrets management

#### Security and Compliance
- **Network Segmentation**: Isolated networks for different service tiers
- **Secrets Management**: Kubernetes secrets with encryption at rest
- **Access Control**: RBAC with fine-grained permissions
- **Audit Logging**: Comprehensive audit trails for compliance requirements

### Negative Consequences

#### Complexity and Overhead
- **Operational Complexity**: Kubernetes cluster management and monitoring
- **Network Overhead**: Inter-service communication latency
- **Resource Overhead**: Container and orchestration layer resource consumption
- **Learning Curve**: Team must understand Kubernetes concepts and operations

#### Cost and Resource Requirements
- **Infrastructure Costs**: Higher resource requirements for containerized deployment
- **Management Overhead**: Additional tooling and monitoring infrastructure
- **Storage Costs**: Persistent volumes for stateful services
- **Network Costs**: Inter-service communication and load balancing

#### Development Complexity
- **Local Development**: Complex local environment setup with multiple services
- **Debugging Challenges**: Distributed system debugging complexity
- **Testing Complexity**: Integration testing across multiple services
- **Configuration Management**: Environment-specific configuration complexity

---

## Alternatives Considered

### Option 1: Monolithic Deployment
**Approach**: Single application container with embedded database connections

**Evaluation**:
- **Pros**: Simpler deployment, easier local development, lower overhead
- **Cons**: No independent scaling, single point of failure, resource conflicts
- **Technical Assessment**: Cannot meet performance and scalability requirements
- **Scalability Impact**: Limited to vertical scaling, no service isolation
- **Framework Integration**: Difficult to optimize for different framework requirements

**Verdict**: **REJECTED** - Cannot meet scalability and performance requirements

### Option 2: Docker Compose Deployment
**Approach**: Docker Compose for service orchestration without Kubernetes

**Evaluation**:
- **Pros**: Simpler than Kubernetes, good for development, familiar Docker concepts
- **Cons**: Limited scaling options, no built-in service discovery, manual failover
- **Operational Impact**: Manual scaling and management, limited monitoring
- **Production Readiness**: Suitable for small deployments, not enterprise scale
- **High Availability**: Requires manual setup, limited automated recovery

**Verdict**: **ACCEPTED for Development**, **REJECTED for Production**

### Option 3: Serverless Architecture
**Approach**: AWS Lambda/Azure Functions for application logic with managed databases

**Evaluation**:
- **Pros**: Automatic scaling, reduced operational overhead, pay-per-use
- **Cons**: Cold start latency, vendor lock-in, limited runtime control
- **Framework Compatibility**: Core SDK may not be compatible with serverless constraints
- **Performance Impact**: Cold starts would violate <500ms response time requirements
- **Cost Analysis**: Potentially higher costs for sustained high-throughput scenarios

**Verdict**: **REJECTED** - Framework compatibility and performance concerns

### Option 4: Virtual Machine Deployment
**Approach**: Traditional VM deployment with manual service management

**Evaluation**:
- **Pros**: Full control over environment, familiar deployment model, no container overhead
- **Cons**: Manual scaling, configuration drift, resource inefficiency
- **Operational Burden**: Manual service management, scaling, and monitoring
- **Resource Efficiency**: Poor resource utilization, difficult capacity planning
- **DevOps Integration**: Limited automation capabilities, manual deployment processes

**Verdict**: **REJECTED** - Cannot meet automation and scalability requirements

---

## Implementation Plan

### Phase 1: Container Development Environment (Week 1)
```bash
# Development infrastructure setup
1. Create Docker development environment
   - Multi-service Docker Compose configuration
   - Development-specific environment variables
   - Volume mounts for code development

2. Service containerization
   - Create Dockerfiles for each service component
   - Optimize container images for development
   - Implement health checks and logging

3. Local testing infrastructure
   - Service discovery and networking
   - Database initialization and migration
   - Integration test setup with real services
```

### Phase 2: Kubernetes Infrastructure (Week 2)
```bash
# Production infrastructure preparation
1. Kubernetes cluster setup
   - Local kind/minikube for development
   - Production cluster configuration
   - Network policies and security groups

2. Service deployment manifests
   - Kubernetes deployments and services
   - ConfigMaps and secrets management
   - Persistent volume claims and storage

3. Monitoring and observability
   - Prometheus metrics collection
   - Grafana dashboards
   - Alerting rules and notifications
```

### Phase 3: Production Deployment (Week 3)
```bash
# Production readiness validation
1. Performance testing
   - Load testing with realistic workloads
   - Database performance optimization
   - Caching strategy implementation

2. Security hardening
   - Network security policies
   - Secrets encryption and rotation
   - Access control and audit logging

3. Operational procedures
   - Deployment automation
   - Backup and restore procedures
   - Incident response playbooks
```

### Deployment Configuration Templates

#### Development Environment (Docker Compose)
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  nexus-api:
    build: 
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/.venv
    environment:
      - ENV=development
      - DEBUG=true
      - RELOAD=true
    depends_on:
      - postgres
      - redis
      - neo4j
      - chromadb

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=kailash_dev
      - POSTGRES_USER=dev_user
      - POSTGRES_PASSWORD=dev_password
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d

  neo4j:
    image: neo4j:5.3-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/dev_password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_dev_data:/data

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chromadb_dev_data:/chroma/chroma

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

volumes:
  postgres_dev_data:
  neo4j_dev_data:
  chromadb_dev_data:
  redis_dev_data:
```

#### Production Environment (Kubernetes)
```yaml
# k8s/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../base
  - postgres.yaml
  - neo4j.yaml
  - chromadb.yaml
  - redis.yaml
  - nexus-api.yaml
  - nexus-websocket.yaml
  - nexus-worker.yaml
  - ingress.yaml
  - monitoring.yaml

configMapGenerator:
  - name: app-config
    literals:
      - ENV=production
      - DEBUG=false
      - LOG_LEVEL=INFO

secretGenerator:
  - name: app-secrets
    literals:
      - DB_PASSWORD=REPLACE_WITH_ACTUAL_PASSWORD
      - NEO4J_PASSWORD=REPLACE_WITH_ACTUAL_PASSWORD
      - OPENAI_API_KEY=REPLACE_WITH_ACTUAL_KEY
      - JWT_SECRET_KEY=REPLACE_WITH_ACTUAL_SECRET

patchesStrategicMerge:
  - production-patches.yaml

images:
  - name: kailash/nexus-api
    newTag: v1.0.0
  - name: kailash/nexus-websocket
    newTag: v1.0.0
  - name: kailash/nexus-worker
    newTag: v1.0.0
```

---

## Risk Mitigation Strategies

### High-Priority Risks

#### Risk: Service Discovery Failures
- **Mitigation**: Kubernetes native service discovery with DNS
- **Backup**: Static IP configuration with health checks
- **Detection**: Service mesh monitoring and alerting
- **Recovery**: Automatic service restart with exponential backoff

#### Risk: Database Connection Pool Exhaustion
- **Mitigation**: Connection pooling with pgbouncer, max connection limits
- **Backup**: Connection timeout and retry logic
- **Detection**: Connection pool metrics and alerting
- **Recovery**: Automatic pool scaling and connection recycling

#### Risk: Inter-Service Communication Latency
- **Mitigation**: Service mesh with traffic management
- **Backup**: Circuit breaker pattern with fallback responses
- **Detection**: Distributed tracing and latency monitoring
- **Recovery**: Load balancing optimization and service scaling

### Medium-Priority Risks

#### Risk: Container Resource Exhaustion
- **Mitigation**: Resource limits and requests, horizontal pod autoscaling
- **Detection**: Resource usage monitoring and alerting
- **Recovery**: Automatic pod scaling and resource reallocation

#### Risk: Configuration Drift
- **Mitigation**: Infrastructure as Code with GitOps
- **Detection**: Configuration validation and drift detection
- **Recovery**: Automated configuration reconciliation

#### Risk: Security Vulnerabilities
- **Mitigation**: Regular security scanning and updates
- **Detection**: Vulnerability scanning in CI/CD pipeline
- **Recovery**: Automated patching and security response procedures

---

## Monitoring and Validation

### Service Health Monitoring
```yaml
# Health check configuration
health_checks:
  nexus-api:
    endpoint: /health
    interval: 30s
    timeout: 5s
    retries: 3
    
  databases:
    postgres:
      query: "SELECT 1"
      interval: 60s
    neo4j:
      query: "RETURN 1"
      interval: 60s
    chromadb:
      endpoint: /api/v1/heartbeat
      interval: 60s
    redis:
      command: "PING"
      interval: 30s
```

### Performance Metrics
```yaml
# Key performance indicators
performance_metrics:
  response_time:
    classification: <500ms (95th percentile)
    recommendations: <2s (95th percentile)
    api_health: <100ms (99th percentile)
    
  throughput:
    requests_per_second: 1000
    concurrent_users: 100
    batch_processing: 1000 items/minute
    
  resource_utilization:
    cpu_usage: <80%
    memory_usage: <85%
    database_connections: <80% of pool
    
  availability:
    uptime: 99.9%
    error_rate: <0.1%
    failover_time: <30s
```

### Alerting Rules
```yaml
# Critical alerts
alerts:
  - name: ServiceDown
    condition: up == 0
    for: 1m
    severity: critical
    
  - name: HighResponseTime
    condition: http_request_duration_seconds > 2
    for: 5m
    severity: warning
    
  - name: DatabaseConnectionHigh
    condition: db_connections_active / db_connections_max > 0.8
    for: 2m
    severity: warning
    
  - name: MemoryUsageHigh
    condition: memory_usage_percent > 85
    for: 5m
    severity: warning
```

---

## Success Criteria

### Technical Success Metrics
- **Service Availability**: 99.9% uptime with <30 second failover
- **Performance Targets**: All SLAs met under realistic load
- **Scalability**: Horizontal scaling demonstrated with load testing
- **Security**: Zero critical vulnerabilities, SOC 2 compliance ready

### Operational Success Metrics
- **Deployment Time**: Zero-downtime deployments in <10 minutes
- **Recovery Time**: <4 hours for full disaster recovery
- **Monitoring Coverage**: 100% service and infrastructure visibility
- **Automation**: 95% automated deployment and scaling operations

### Business Success Metrics
- **Multi-Framework Integration**: Core SDK + DataFlow + Nexus working seamlessly
- **Classification Performance**: >95% accuracy with <500ms response time
- **Multi-Channel Access**: API + CLI + MCP simultaneously operational
- **Developer Experience**: <1 hour from code commit to production deployment

---

## Conclusion

The containerized microservices architecture with Kubernetes orchestration provides the optimal balance of scalability, reliability, and operational efficiency for the multi-framework Kailash SDK implementation.

This architecture enables:
- **Independent scaling** of Core SDK, DataFlow, and Nexus components
- **High availability** with automated failover and recovery
- **Performance optimization** through dedicated resource allocation
- **Security compliance** with network segmentation and secrets management
- **Operational excellence** through comprehensive monitoring and automation

**Status**: Ready for implementation approval  
**Next Steps**: Begin Phase 1 container development environment setup following implementation plan