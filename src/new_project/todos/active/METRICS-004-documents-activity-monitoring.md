# METRICS-004-Documents-Activity-Monitoring

## Description
Set up real-time document processing tracking with file upload/modification events, document categorization, storage monitoring, and activity feeds for business insights.

## Current State Analysis
- documents.db exists with document metadata
- production_business_metrics_server.py has documents endpoints
- Need real-time file activity monitoring
- Document processing metrics for business intelligence

## Acceptance Criteria
- [ ] Real-time document upload/modification tracking
- [ ] Document categorization and tagging system
- [ ] Storage usage monitoring and alerts
- [ ] Recent document activity feed
- [ ] Document processing performance metrics
- [ ] Integration with customer/project context

## Dependencies
- METRICS-001 (database schemas validated)
- documents.db with proper schema
- File system monitoring capabilities

## Risk Assessment
- **HIGH**: File system monitoring could impact performance with large document volumes
- **MEDIUM**: Document categorization accuracy depends on file content analysis
- **LOW**: Storage monitoring alerts could generate false positives

## Subtasks
- [ ] File System Monitoring (Est: 1h) - Implement real-time file upload/change detection
  - Verification: System detects document uploads and modifications immediately
- [ ] Document Categorization (Est: 45min) - Auto-categorize documents by type and content
  - Verification: Documents automatically tagged with appropriate categories
- [ ] Storage Usage Tracking (Est: 30min) - Monitor storage usage with threshold alerts
  - Verification: Storage metrics accurate and alerts trigger at defined thresholds
- [ ] Activity Feed Implementation (Est: 45min) - Create real-time document activity stream
  - Verification: Activity feed shows recent document operations with proper context
- [ ] Performance Metrics (Est: 30min) - Track document processing speed and success rates
  - Verification: Processing metrics collected and displayed accurately

## Testing Requirements
- [ ] Unit tests: Document categorization accuracy
- [ ] Integration tests: File system monitoring performance
- [ ] E2E tests: Complete document lifecycle tracking

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Real-time document activity monitoring operational
- [ ] Document categorization working accurately
- [ ] Storage usage monitored with proper alerts
- [ ] Activity feed provides meaningful business insights
- [ ] Performance metrics tracked for optimization

## Specialist Assignment
- **file-monitoring-specialist**: Implement file system monitoring
- **ai-categorization-specialist**: Handle document auto-categorization
- **performance-monitoring**: Track processing performance metrics

## Execution Commands
```bash
# 1. Validate documents database schema
python -c "import sqlite3; conn = sqlite3.connect('documents.db'); print(conn.execute('SELECT sql FROM sqlite_master WHERE name=\"documents\"').fetchone())"

# 2. Test documents API endpoints
curl http://localhost:3002/metrics/documents

# 3. Start document monitoring service
python src/new_project/start_document_monitoring.py

# 4. Test document upload tracking
curl -X POST http://localhost:3002/documents/upload -F "file=@test_document.pdf"

# 5. Validate activity feed
curl http://localhost:3002/documents/activity
```

## Document Monitoring Features
```python
# Document activity event format:
{
    "type": "document_activity",
    "event": "upload|modify|access|delete",
    "data": {
        "document_id": 789,
        "title": "Q4 Sales Proposal",
        "category": "sales",
        "file_size": 2048576,
        "created_by": "john.doe",
        "timestamp": "2024-08-05T14:30:00Z",
        "customer_id": 1,
        "tags": ["proposal", "q4", "sales"]
    }
}

# Storage monitoring thresholds:
{
    "storage_limits": {
        "warning_threshold": "80%",
        "critical_threshold": "95%",
        "max_file_size": "100MB",
        "retention_policy": "2_years"
    }
}
```

## Auto-categorization Rules
- **Proposals**: Files containing "proposal", "quote", "bid"
- **Contracts**: Files with "contract", "agreement", "terms"
- **Reports**: Files with "report", "analysis", "summary"
- **Technical**: Files with "specification", "technical", "architecture"
- **Financial**: Files with "invoice", "budget", "financial", "roi"