# FRONTEND-001-Fix-Frontend-500-Errors

## Description
Resolve frontend 500 errors by updating the API client configuration to connect to the deployed backend services. The frontend is currently running but showing 500 errors due to missing backend API connections.

## Acceptance Criteria
- [ ] Frontend loads without 500 internal server errors
- [ ] API client successfully connects to backend on port 8000
- [ ] Environment variables properly configured for production
- [ ] Error handling shows meaningful messages instead of 500 errors
- [ ] All frontend routes accessible and functional
- [ ] WebSocket connection to MCP server operational

## Dependencies
- BACKEND-001: Nexus backend API operational on port 8000
- MCP-001: MCP server running and accepting connections
- Frontend Docker container running

## Risk Assessment
- **HIGH**: Hardcoded API endpoints pointing to wrong URLs
- **MEDIUM**: CORS issues preventing API communication
- **MEDIUM**: Missing environment variables causing undefined behavior
- **LOW**: Frontend build cache causing stale configurations

## Subtasks
- [ ] Analyze current frontend error logs (Est: 15min) - Identify specific API connection failures
- [ ] Update API client configuration (Est: 30min) - Point to correct backend endpoints
- [ ] Configure environment variables (Est: 15min) - Set NEXT_PUBLIC_API_URL and NEXT_PUBLIC_MCP_URL
- [ ] Update Docker environment configuration (Est: 15min) - Production environment settings
- [ ] Implement proper error handling (Est: 30min) - Replace 500 errors with meaningful messages
- [ ] Test API connectivity (Est: 15min) - Verify all endpoints accessible
- [ ] Rebuild and restart frontend container (Est: 15min) - Apply configuration changes

## Environment Variables Required
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MCP_URL=ws://localhost:3000
NODE_ENV=production
```

## API Client Updates Required
- Update base URL for REST API calls
- Configure WebSocket client for MCP server
- Add proper error handling for network failures
- Implement retry logic for failed requests
- Add loading states for API operations

## Docker Configuration
```dockerfile
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_MCP_URL=ws://localhost:3000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_MCP_URL=$NEXT_PUBLIC_MCP_URL
```

## Testing Requirements
- [ ] Unit tests: API client configuration validates correctly
- [ ] Integration tests: Frontend to backend API communication works
- [ ] E2E tests: Full user workflows complete without errors

## API Endpoints to Test
- GET /health - Backend health check
- POST /auth/login - User authentication
- GET /api/v1/workflows - Workflow listing
- WebSocket connection to MCP server

## Error Handling Improvements
- Replace generic 500 errors with specific error messages
- Add network connectivity error handling
- Implement graceful degradation for offline scenarios
- Show loading states during API requests
- Add retry buttons for failed operations

## Definition of Done
- [ ] Frontend loads successfully without 500 errors
- [ ] All API endpoints accessible from frontend
- [ ] Environment variables configured correctly
- [ ] WebSocket connection to MCP server working
- [ ] Error messages are user-friendly and actionable
- [ ] Loading states implemented for all API operations
- [ ] Frontend container rebuilt with new configuration
- [ ] All major user workflows functional
- [ ] Ready for FRONTEND-002 (Environment Configuration)