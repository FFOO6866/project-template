# METRICS-003-Active-Quotations-Tracking

## Description
Implement real-time active quotations tracking with WebSocket updates for quotations status changes, expiring quotes alerts, and pipeline value monitoring.

## Current State Analysis
- quotations.db exists with basic schema
- production_business_metrics_server.py has quotations endpoints
- Need real-time updates for quotation status changes
- Expiring quotations alerting system needed

## Acceptance Criteria
- [ ] Real-time quotations status tracking (draft → active → sent → negotiation → closed)
- [ ] WebSocket notifications for quotation status changes
- [ ] Expiring quotations alerts (7-day window)
- [ ] Pipeline value updates in real-time
- [ ] Quotations dashboard with filtering and sorting
- [ ] Integration with customer data for context

## Dependencies
- METRICS-001 (database schemas validated)
- quotations.db with proper schema
- WebSocket server infrastructure

## Risk Assessment
- **HIGH**: Real-time updates could overwhelm frontend with too many WebSocket messages
- **MEDIUM**: Quotation status workflow logic needs careful validation
- **LOW**: Date handling for expiration alerts could have timezone issues

## Subtasks
- [ ] Quotations WebSocket Server (Est: 1h) - Implement WebSocket endpoints for real-time updates
  - Verification: WebSocket server broadcasts quotation status changes
- [ ] Status Change Tracking (Est: 45min) - Track quotation lifecycle with timestamps
  - Verification: All status transitions logged with proper workflow validation
- [ ] Expiring Quotes Alerts (Est: 30min) - Automated alerts for quotes expiring within 7 days
  - Verification: Alert system identifies and notifies about expiring quotations
- [ ] Pipeline Value Monitoring (Est: 30min) - Real-time pipeline value calculations
  - Verification: Pipeline values update automatically when quotations change
- [ ] Quotations Dashboard (Est: 1h) - Interactive dashboard for quotation management
  - Verification: Dashboard shows real-time quotations with proper filtering

## Testing Requirements
- [ ] Unit tests: Quotation status workflow validation
- [ ] Integration tests: WebSocket updates propagate correctly
- [ ] E2E tests: Full quotation lifecycle from creation to closure

## Definition of Done
- [ ] All acceptance criteria met
- [ ] WebSocket server operational for quotations updates
- [ ] Expiring quotations identified and alerts sent
- [ ] Pipeline values calculate correctly in real-time
- [ ] Dashboard shows live quotations data
- [ ] Status change workflow validates properly

## Specialist Assignment
- **websocket-specialist**: Implement real-time WebSocket communications
- **dataflow-specialist**: Handle quotation workflow and data validation
- **frontend-specialist**: Create quotations dashboard interface

## Execution Commands
```bash
# 1. Validate quotations database schema
python -c "import sqlite3; conn = sqlite3.connect('quotations.db'); print(conn.execute('SELECT sql FROM sqlite_master WHERE name=\"quotations\"').fetchone())"

# 2. Test quotations API endpoints
curl http://localhost:3002/metrics/quotations

# 3. Start WebSocket server for quotations
python src/new_project/start_quotations_websocket.py

# 4. Test quotation status updates
curl -X POST http://localhost:3002/quotations/update-status -d '{"quote_id": 1, "status": "negotiation"}'

# 5. Validate expiring quotes detection
curl http://localhost:3002/quotations/expiring
```

## Real-time Features Implementation
```python
# WebSocket message format for quotation updates:
{
    "type": "quotation_update",
    "data": {
        "quote_id": 123,
        "status": "negotiation",
        "previous_status": "sent",
        "timestamp": "2024-08-05T14:30:00Z",
        "customer": "Acme Corp",
        "value": 450000
    }
}

# Expiring quotations alert format:
{
    "type": "expiring_alert",
    "data": {
        "quote_id": 456,
        "days_until_expiry": 3,
        "customer": "TechStart Solutions",
        "value": 280000,
        "expires_on": "2024-08-08"
    }
}
```