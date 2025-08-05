# ADR-002: Frontend-Backend Integration Architecture

## Status
**Proposed**

## Context
The sales assistant platform requires seamless integration between a Next.js frontend and an AI-powered MCP (Model Context Protocol) server backend. Based on ultrathink analysis, this is a HIGH complexity integration (28/40 points) with several critical integration challenges:

### Current State Analysis
- **Frontend**: Next.js 15 with React 19, TypeScript, comprehensive UI components
- **Backend**: Complete MCP server with AI capabilities, DataFlow models, Nexus platform
- **Gap**: Missing MCP client integration layer, incomplete WebSocket implementation, no authentication flow

### Integration Challenges
1. **Real-time AI Processing**: Document processing and quote generation can take 30+ seconds
2. **MCP Protocol Complexity**: Need bidirectional MCP communication for AI agents
3. **WebSocket Architecture**: Real-time updates for chat, document processing, notifications
4. **File Upload Streaming**: Large documents (50MB+) with progress tracking
5. **Error Handling**: Graceful degradation with retry mechanisms

### Requirements
- Response time targets: <2s for chat, <30s for document processing
- Support for concurrent users with session management
- Mobile responsiveness and accessibility compliance
- Offline capability for essential features

## Decision
We will implement a **Hybrid Architecture** combining MCP protocol with REST API and WebSocket layers.

### Core Architecture Components

#### 1. **MCP Client Integration Layer**
```typescript
// Frontend MCP client for AI workflows
class MCPClient {
  async callTool(toolName: string, params: object): Promise<MCPResponse>
  async getResource(uri: string): Promise<MCPResource>
  async streamTool(toolName: string, params: object): AsyncIterator<MCPProgress>
}
```

#### 2. **REST API Gateway Layer**
```typescript
// HTTP API for standard CRUD operations
interface APILayer {
  auth: AuthenticationAPI
  documents: DocumentAPI
  customers: CustomerAPI
  quotes: QuoteAPI
  analytics: AnalyticsAPI
}
```

#### 3. **WebSocket Real-time Layer**
```typescript
// Real-time updates and chat interface
interface WebSocketAPI {
  chat: ChatWebSocketHandler
  notifications: NotificationHandler
  progress: ProgressTracker
  presence: PresenceManager
}
```

#### 4. **Authentication & Session Management**
```typescript
// JWT-based authentication with session persistence
interface AuthSystem {
  login(credentials: LoginRequest): Promise<AuthResponse>
  refreshToken(): Promise<TokenResponse>
  validateSession(): Promise<SessionData>
}
```

### Key Architectural Decisions

#### **Decision 1: Three-Tier Communication Architecture**
- **Tier 1**: REST API for standard operations (CRUD, file upload)
- **Tier 2**: WebSocket for real-time updates (chat, progress, notifications)
- **Tier 3**: MCP Protocol for AI agent interactions (tool calls, resources)

#### **Decision 2: Progressive Enhancement Pattern**
- Basic functionality works without WebSocket (graceful degradation)
- Enhanced experience with real-time features
- Offline-first for essential read operations

#### **Decision 3: File Upload Strategy**
- Multipart upload for large files (chunked)
- Real-time progress via WebSocket
- Background processing with status updates

#### **Decision 4: Error Handling Framework**
- Circuit breaker pattern for API resilience
- Exponential backoff for retry logic
- User-friendly error messages with recovery actions

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)
1. **MCP Client Library**
   - TypeScript MCP client implementation
   - Connection pooling and error handling
   - Tool discovery and execution

2. **Authentication Integration**
   - JWT token management
   - Secure token storage (httpOnly cookies)
   - Session validation middleware

3. **Basic API Layer**
   - Document upload/download endpoints
   - Customer and quote CRUD operations
   - Health checks and monitoring

### Phase 2: Real-time Features (Week 3-4)
1. **WebSocket Integration**
   - Chat interface with message persistence
   - Real-time document processing updates
   - System notifications

2. **File Processing Pipeline**
   - Chunked file upload with progress
   - Background AI processing
   - Status notifications via WebSocket

### Phase 3: Advanced Features (Week 5-6)
1. **Advanced AI Integration**
   - MCP tool chaining for complex workflows
   - RAG-powered document Q&A
   - Intelligent quote generation

2. **Performance Optimization**
   - Client-side caching strategies
   - Response compression
   - Connection pooling

## Technical Specifications

### API Endpoint Structure
```
/api/v1/
├── auth/
│   ├── login
│   ├── refresh
│   └── logout
├── files/
│   ├── upload
│   ├── download/{id}
│   └── status/{id}
├── mcp/
│   ├── tools
│   ├── execute
│   └── resources
├── documents/
├── customers/
├── quotes/
└── analytics/
```

### WebSocket Event Schema
```typescript
interface WebSocketEvent {
  type: 'chat_message' | 'document_progress' | 'notification' | 'presence_update'
  data: object
  timestamp: string
  session_id: string
}
```

### MCP Integration Points
```typescript
// Key MCP tools to integrate
const MCPTools = {
  'process_document': DocumentProcessingTool,
  'generate_quote': QuoteGenerationTool,
  'ask_document_question': DocumentQATool,
  'chat_with_assistant': ChatAssistantTool,
  'search_customers': CustomerSearchTool,
  'get_sales_analytics': AnalyticsTool
}
```

## Consequences

### Positive
- **Scalable Architecture**: Clean separation of concerns
- **Real-time Capabilities**: Enhanced user experience with live updates
- **AI Integration**: Full access to sophisticated AI workflows
- **Performance**: Optimized for both speed and reliability
- **Maintainability**: Clear architectural boundaries

### Negative
- **Complexity**: Three different communication protocols to manage
- **Development Time**: Initial setup requires 4-6 weeks
- **Resource Usage**: Higher memory/CPU usage due to WebSocket connections
- **Testing Complexity**: Need integration tests across multiple protocols

### Technical Debt
- **Connection Management**: Need robust connection pooling and cleanup
- **Error Correlation**: Tracking errors across multiple communication layers
- **Monitoring**: Comprehensive observability across REST/WebSocket/MCP

## Alternatives Considered

### Option 1: Pure REST API
- **Pros**: Simple implementation, well-understood patterns
- **Cons**: No real-time updates, poor UX for long-running AI operations
- **Rejection Reason**: User experience requirements mandate real-time features

### Option 2: WebSocket-Only Architecture
- **Pros**: Single communication protocol, real-time by default
- **Cons**: Complex error handling, poor mobile support, debugging difficulties
- **Rejection Reason**: Mobile responsiveness and reliability requirements

### Option 3: GraphQL with Subscriptions
- **Pros**: Type-safe queries, real-time subscriptions, efficient data loading
- **Cons**: Additional complexity, learning curve, MCP protocol incompatibility
- **Rejection Reason**: Doesn't integrate well with existing MCP infrastructure

## Implementation Plan

### Dependencies
- MCP client library (custom implementation required)
- WebSocket client with reconnection logic
- JWT authentication middleware
- File upload progress tracking

### Testing Strategy
- **Unit Tests**: Individual API endpoints and MCP tools
- **Integration Tests**: End-to-end workflows with real MCP server
- **Performance Tests**: Load testing with concurrent users
- **User Acceptance Tests**: Complete user workflows

### Monitoring & Observability
- API response time monitoring
- WebSocket connection health
- MCP tool execution metrics
- User session analytics

### Success Criteria
- **Performance**: <2s API response time, <500ms WebSocket latency
- **Reliability**: 99.9% uptime, <0.1% error rate
- **User Experience**: <5s time to first interaction, seamless real-time updates
- **Scalability**: Support 100+ concurrent users

---

*This ADR provides the architectural foundation for building a production-ready frontend-backend integration that leverages the full capabilities of the AI-powered sales assistant platform.*