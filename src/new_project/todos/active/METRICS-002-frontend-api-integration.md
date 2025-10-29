# METRICS-002-Frontend-API-Integration

## Description
Connect the frontend metrics-bar.tsx component to the production business metrics server (port 3002) to display real-time business data instead of hardcoded values.

## Current State Analysis
- Frontend has hardcoded metrics in metrics-bar.tsx
- Production business metrics server running on port 3002
- Need to create API client for real-time data fetching
- WebSocket integration for live updates

## Acceptance Criteria
- [ ] Frontend API client connects to production metrics server
- [ ] metrics-bar.tsx displays real business data (quotations, documents, sales)
- [ ] Real-time updates via WebSocket or polling
- [ ] Error handling for API connection failures
- [ ] Loading states during data fetch
- [ ] Responsive design maintained with dynamic data

## Dependencies
- METRICS-001 (database schemas must be fixed first)
- Frontend running on port 3000
- Production metrics server on port 3002

## Risk Assessment
- **HIGH**: CORS issues could prevent frontend from accessing metrics API
- **MEDIUM**: API response format changes could break frontend display
- **LOW**: Network latency might affect real-time updates

## Subtasks
- [ ] API Client Implementation (Est: 1h) - Create metrics API client with error handling
  - Verification: API client successfully fetches data from all metrics endpoints
- [ ] Frontend Component Updates (Est: 45min) - Update metrics-bar.tsx to use real data
  - Verification: Component displays live business metrics instead of hardcoded values
- [ ] Real-time Updates (Est: 1h) - Implement WebSocket or polling for live updates
  - Verification: Metrics update automatically when backend data changes
- [ ] Error Handling & Loading States (Est: 30min) - Add proper error boundaries and loading indicators
  - Verification: Frontend gracefully handles API failures and shows loading states

## Testing Requirements
- [ ] Unit tests: API client handles all response formats correctly
- [ ] Integration tests: Frontend successfully connects to metrics server
- [ ] E2E tests: User sees real business metrics on dashboard

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Frontend displays real quotations count from database
- [ ] Live document processing metrics shown
- [ ] Sales pipeline values updated from production data
- [ ] Error handling works for API failures
- [ ] No CORS or connection issues

## Specialist Assignment
- **frontend-specialist**: Handle React component updates and API integration
- **nexus-specialist**: Ensure proper API endpoint configuration
- **testing-specialist**: Create frontend integration tests

## Execution Commands
```bash
# 1. Test metrics API endpoints
curl http://localhost:3002/metrics/business

# 2. Update frontend environment
echo 'NEXT_PUBLIC_METRICS_API=http://localhost:3002' >> fe-reference/.env.local

# 3. Install frontend dependencies
cd fe-reference && npm install

# 4. Test frontend API connection
cd fe-reference && npm run dev

# 5. Validate metrics display
curl http://localhost:3000/api/health
```

## API Integration Details
```typescript
// Required API endpoints to integrate:
// GET /metrics/business - Complete business metrics
// GET /metrics/quotations - Active quotations data  
// GET /metrics/documents - Recent documents activity
// GET /dashboard - Executive dashboard summary
```