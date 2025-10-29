# Product Requirements Document (PRD)
# Email-Based Quotation Request Module

**Version**: 1.0
**Date**: 2025-10-22
**Author**: System Analysis
**Status**: Draft for Review

---

## Executive Summary

This PRD outlines the development of an automated email monitoring system that detects incoming customer quotation requests, intelligently extracts requirements using AI, and populates them in the dashboard for streamlined quotation processing.

### Business Value
- **Reduce Manual Entry**: Eliminate manual document upload for email-based RFQs
- **Faster Response Time**: Automatically process incoming requests within minutes
- **24/7 Availability**: Monitor email inbox continuously without human intervention
- **Seamless Integration**: Leverage 100% of existing AI quotation processing pipeline
- **Enhanced Customer Experience**: Faster turnaround on quotation requests

---

## 1. Background & Context

### 1.1 Current State Analysis

**Existing Quotation Flow**:
```
Document Upload (Manual) → Text Extraction → AI Analysis →
Product Matching → Pricing → Quotation Generation → PDF Creation
```

**Key Infrastructure**:
- **Backend**: FastAPI (nexus_backend_api.py) with PostgreSQL + Redis
- **AI Processing**: OpenAI GPT-4 Turbo for requirement extraction
- **Document Processor**: Handles PDF, DOCX, TXT formats
- **Product Matching**: 17,266 products in catalog with fuzzy matching
- **Quotation Generator**: Professional PDF generation with ReportLab
- **Frontend**: Next.js dashboard with "Recent Documents" section

**Current Limitations**:
1. Manual file upload required - no email integration
2. "Recent Documents" shows uploaded files only
3. No email tracking or monitoring capability
4. No email attachment processing workflow

### 1.2 Email Infrastructure

**Mail Server Configuration**:
- **Webmail Interface**: https://webmail.horme.com.sg/
- **Business Email**: integrum@horme.com.sg
- **Protocol Support**: IMAP/SMTP (to be verified)
- **Use Case**: Monitor for customer quotation requests

---

## 2. Product Vision & Goals

### 2.1 Vision Statement
> Automatically transform customer email requests into actionable quotation entries, enabling sales teams to respond faster and more accurately to business opportunities.

### 2.2 Success Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Email Processing Time | < 5 minutes | Time from email receipt to dashboard entry |
| AI Extraction Accuracy | > 90% | Manual review of extracted requirements |
| Attachment Processing Rate | 100% | Successfully processed attachments / total |
| False Positive Rate | < 5% | Non-RFQ emails incorrectly flagged |
| System Uptime | 99.5% | Email monitoring service availability |

### 2.3 Out of Scope (V1)
- ❌ Email sending/SMTP outbound functionality
- ❌ Multi-inbox monitoring (only integrum@horme.com.sg)
- ❌ Email threading/conversation tracking
- ❌ Automatic quotation approval/sending
- ❌ CRM integration (Salesforce, HubSpot, etc.)
- ❌ Email template management

---

## 3. User Stories & Requirements

### 3.1 Primary User Stories

**US-01: Automatic Email Detection**
```
As a Sales Manager
I want incoming RFQ emails to be automatically detected
So that I don't miss any customer quotation requests
```
**Acceptance Criteria**:
- ✅ System checks email inbox every 5 minutes
- ✅ New emails with RFQ-related keywords are flagged
- ✅ Email metadata (sender, subject, date) is captured
- ✅ Unread emails are prioritized over read emails

---

**US-02: Smart Content Extraction**
```
As a Sales Manager
I want the system to extract product requirements from email body and attachments
So that I can quickly review and approve quotations
```
**Acceptance Criteria**:
- ✅ Email body text is analyzed by AI
- ✅ PDF/DOCX/Excel attachments are processed
- ✅ Product items, quantities, specifications extracted
- ✅ Customer name and contact info captured
- ✅ Confidence score provided for extraction quality

---

**US-03: Dashboard Integration - "New Quotation Requests"**
```
As a Sales Manager
I want new email-based requests to appear in a dedicated dashboard section
So that I can prioritize and process them efficiently
```
**Acceptance Criteria**:
- ✅ Dashboard shows "New Quotation Requests" section (renamed from "Recent Documents")
- ✅ Displays: Date/Time, Customer Name, Email, Request Summary
- ✅ Click to view full extracted requirements
- ✅ Trigger quotation processing flow identical to manual uploads
- ✅ Mark as "Processed" or "Ignored"

---

**US-04: Attachment Handling**
```
As a Sales Manager
I want email attachments to be processed the same as uploaded documents
So that I receive the same quality of AI analysis
```
**Acceptance Criteria**:
- ✅ Attachments downloaded to secure temp directory
- ✅ Processed using existing DocumentProcessor service
- ✅ Multiple attachments consolidated into single request
- ✅ Unsupported formats logged with error notification

---

**US-05: Duplicate Prevention**
```
As a Sales Manager
I want to avoid processing the same email multiple times
So that I don't create duplicate quotations
```
**Acceptance Criteria**:
- ✅ Email Message-ID tracked in database
- ✅ Re-processing same email is blocked
- ✅ Forward/Reply chains detected and handled
- ✅ Manual re-process option available if needed

---

## 4. Technical Requirements

### 4.1 Email Monitoring Service

**Architecture Pattern**: Background service running in Docker container

**Core Requirements**:
```python
# MANDATORY REQUIREMENTS
✅ Use IMAP protocol (imapclient library)
✅ Poll interval: 5 minutes (configurable via ENV)
✅ Secure credential storage (environment variables only)
✅ Graceful error handling (no silent failures)
✅ Comprehensive logging (structured logs)
✅ Health check endpoint for monitoring
✅ Automatic reconnection on connection loss
✅ NO MOCK DATA - All real email processing
```

**Email Classification Logic**:
```python
RFQ_KEYWORDS = [
    "quotation", "quote", "rfq", "rfp", "request for quotation",
    "request for proposal", "pricing", "price list", "estimate",
    "proposal", "bid", "tender"
]

ATTACHMENT_TYPES = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"]
```

### 4.2 Database Schema Extensions

**New Table: `email_quotation_requests`**
```sql
CREATE TABLE email_quotation_requests (
    id SERIAL PRIMARY KEY,

    -- Email Metadata
    message_id VARCHAR(500) UNIQUE NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    subject VARCHAR(500) NOT NULL,
    received_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Email Content
    body_text TEXT,
    body_html TEXT,
    has_attachments BOOLEAN DEFAULT false,
    attachment_count INTEGER DEFAULT 0,

    -- Processing Status
    status VARCHAR(50) DEFAULT 'pending',
    -- pending, processing, completed, failed, ignored

    -- AI Extraction Results
    extracted_requirements JSONB,
    ai_confidence_score DECIMAL(3,2),
    extracted_at TIMESTAMP WITH TIME ZONE,

    -- Linked Records
    document_id INTEGER REFERENCES documents(id),
    quotation_id INTEGER REFERENCES quotations(id),
    customer_id INTEGER REFERENCES customers(id),

    -- Metadata
    processing_notes TEXT,
    error_message TEXT,
    processed_by INTEGER REFERENCES users(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_email_quotation_message_id (message_id),
    INDEX idx_email_quotation_status (status),
    INDEX idx_email_quotation_received_date (received_date DESC),
    INDEX idx_email_quotation_sender (sender_email)
);

COMMENT ON TABLE email_quotation_requests IS
'Stores incoming email-based quotation requests with AI extraction results';
```

**New Table: `email_attachments`**
```sql
CREATE TABLE email_attachments (
    id SERIAL PRIMARY KEY,
    email_request_id INTEGER NOT NULL REFERENCES email_quotation_requests(id) ON DELETE CASCADE,

    -- File Information
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),

    -- Processing Status
    processed BOOLEAN DEFAULT false,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,

    -- Link to documents table
    document_id INTEGER REFERENCES documents(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_email_attachments_request (email_request_id),
    INDEX idx_email_attachments_processed (processed)
);

COMMENT ON TABLE email_attachments IS
'Stores email attachments linked to quotation requests';
```

### 4.3 API Endpoints

**New Endpoints in nexus_backend_api.py**:

```python
# GET /api/email-quotation-requests
# Returns list of email-based quotation requests
# Query params: status, limit, offset

# GET /api/email-quotation-requests/{id}
# Returns specific email request with full details

# POST /api/email-quotation-requests/{id}/process
# Trigger quotation processing flow for email request

# PUT /api/email-quotation-requests/{id}/status
# Update status (mark as processed, ignored, etc.)

# GET /api/email-quotation-requests/recent
# PUBLIC endpoint for dashboard "New Quotation Requests" section

# POST /api/email-quotation-requests/{id}/reprocess
# Manually reprocess an email request
```

### 4.4 Frontend Updates

**Dashboard Changes** (`frontend/app/page.tsx`):

```typescript
// RENAME SECTION
OLD: <RecentDocuments onDocumentSelect={...} />
NEW: <NewQuotationRequests onRequestSelect={...} />

// NEW COMPONENT: NewQuotationRequests
interface EmailQuotationRequest {
  id: number;
  received_date: string;
  sender_name: string;
  sender_email: string;
  subject: string;
  status: string;
  ai_confidence_score: number;
  attachment_count: number;
}

// DISPLAY FIELDS
- Date/Time (received_date)
- Customer Name (sender_name or extracted customer)
- Email Address (sender_email)
- Quotation Request Summary (subject + extracted requirements preview)
- Status Badge (pending, processing, completed, failed)
- Confidence Score indicator
- Click to open full request and trigger processing
```

---

## 5. System Architecture

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Email Server (IMAP)                      │
│               integrum@horme.com.sg                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ IMAP Protocol (Poll every 5 min)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            Email Monitoring Service (Docker)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Fetch new emails                                 │  │
│  │  2. Filter RFQ-related messages                      │  │
│  │  3. Download attachments                             │  │
│  │  4. Store in email_quotation_requests table          │  │
│  │  5. Trigger background processing                    │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Database Insert
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  email_quotation_requests                          │    │
│  │  email_attachments                                 │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ FastAPI Background Task
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          Existing Quotation Processing Pipeline              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DocumentProcessor (Email body + Attachments)        │  │
│  │          ↓                                           │  │
│  │  OpenAI Requirement Extraction                       │  │
│  │          ↓                                           │  │
│  │  Product Matcher (17,266 products)                   │  │
│  │          ↓                                           │  │
│  │  Pricing Calculator                                  │  │
│  │          ↓                                           │  │
│  │  Quotation Generator + PDF                           │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Dashboard API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Frontend Dashboard (Next.js)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  "New Quotation Requests" Section                    │  │
│  │  - Date/Time                                         │  │
│  │  - Customer Name & Email                             │  │
│  │  - Request Summary                                   │  │
│  │  - Click → Trigger Processing Flow                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Processing Flow

```
1. EMAIL MONITORING (Every 5 minutes)
   ├── Connect to IMAP server
   ├── Search for UNSEEN messages
   ├── Filter by RFQ keywords in subject/body
   └── For each RFQ email:
       ├── Extract metadata (sender, subject, date, message-id)
       ├── Download email body (text + HTML)
       ├── Download attachments to /app/email-attachments/
       ├── Insert into email_quotation_requests table
       └── Trigger background processing task

2. BACKGROUND PROCESSING
   ├── Create temporary document entry
   ├── Process email body as text document
   ├── Process each attachment using DocumentProcessor
   ├── Merge results from body + attachments
   ├── Run AI requirement extraction (OpenAI GPT-4)
   ├── Calculate confidence score
   ├── Update email_quotation_requests with results
   └── Set status to 'completed' or 'failed'

3. DASHBOARD DISPLAY
   ├── API endpoint returns top 20 recent email requests
   ├── Frontend displays in "New Quotation Requests"
   ├── User clicks on request
   ├── Show extracted requirements
   └── User clicks "Process Quotation"
       └── Triggers full quotation generation flow

4. QUOTATION GENERATION (User-Initiated)
   ├── Use extracted requirements from email
   ├── Match products from catalog
   ├── Calculate pricing
   ├── Generate quotation PDF
   ├── Link quotation to email_quotation_requests
   └── Update status to 'quotation_created'
```

---

## 6. Security & Compliance

### 6.1 Security Requirements

**Credential Management**:
```bash
# .env file (NEVER commit to git)
EMAIL_IMAP_SERVER=webmail.horme.com.sg
EMAIL_IMAP_PORT=993
EMAIL_USERNAME=integrum@horme.com.sg
EMAIL_PASSWORD=integrum2@25  # SECURE STORAGE ONLY
EMAIL_USE_SSL=true
```

**Data Protection**:
- ✅ Email attachments stored in secure directory (`/app/email-attachments/`)
- ✅ File permissions: 600 (owner read/write only)
- ✅ Automatic cleanup of processed attachments after 30 days
- ✅ Email credentials encrypted at rest (consider HashiCorp Vault for production)
- ✅ SSL/TLS for all email connections
- ✅ No email content logged (only metadata)

**Access Control**:
- ✅ Email monitoring service runs as non-root user in Docker
- ✅ Database access via connection pool with limited privileges
- ✅ API endpoints require JWT authentication (except public dashboard endpoint)

### 6.2 Error Handling

**Email Connection Failures**:
```python
# Retry logic with exponential backoff
MAX_RETRIES = 3
RETRY_DELAY = [30, 60, 120]  # seconds

# Alert on persistent failures
if retries_exhausted:
    log_critical_error()
    send_slack_alert()  # Optional
```

**Processing Failures**:
```python
# Capture all errors in email_quotation_requests.error_message
# Set status to 'failed'
# Allow manual reprocess via API
# NO SILENT FAILURES - All errors logged and visible
```

---

## 7. Performance & Scalability

### 7.1 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Email Fetch Time | < 10 seconds | Per polling cycle |
| Attachment Download | < 30 seconds | Per attachment (up to 10MB) |
| AI Processing Time | < 60 seconds | Per email (body + attachments) |
| Database Insert | < 1 second | Per email record |
| Dashboard Load Time | < 2 seconds | 20 most recent requests |

### 7.2 Scalability Considerations

**Current Scope (V1)**:
- Single inbox monitoring
- ~50-100 emails/day expected
- ~5-10 RFQ emails/day expected
- Sequential processing (no parallel processing needed)

**Future Scaling (V2+)**:
- Multi-inbox support (use Redis queue for coordination)
- Parallel processing of attachments
- Email archival strategy (move processed emails to subfolder)
- Database partitioning by date for large volumes

---

## 8. Testing Strategy

### 8.1 Test Coverage Requirements

**Unit Tests** (Tier 1):
```python
# src/services/test_email_monitor.py
✅ test_parse_email_headers()
✅ test_detect_rfq_keywords()
✅ test_extract_sender_info()
✅ test_download_attachment()
✅ test_duplicate_detection()
```

**Integration Tests** (Tier 2):
```python
# tests/integration/test_email_quotation_flow.py
✅ test_email_fetch_and_store()
✅ test_attachment_processing_pipeline()
✅ test_ai_extraction_from_email()
✅ test_dashboard_api_integration()
✅ test_quotation_generation_from_email()

# REAL INFRASTRUCTURE REQUIRED
# - Test PostgreSQL instance
# - Mock IMAP server (dovecot in Docker)
# - Real OpenAI API calls (test API key)
```

**End-to-End Tests** (Tier 3):
```python
# tests/e2e/test_complete_email_rfq_flow.py
✅ test_send_rfq_email_to_monitoring_address()
✅ test_wait_for_email_detection()
✅ test_verify_dashboard_display()
✅ test_trigger_quotation_from_dashboard()
✅ test_verify_quotation_pdf_generated()
```

### 8.2 Test Data

**Sample Test Emails**:
```
test-data/email-rfq-001.eml  # Simple text RFQ
test-data/email-rfq-002.eml  # RFQ with PDF attachment
test-data/email-rfq-003.eml  # RFQ with multiple attachments
test-data/email-non-rfq.eml  # Non-RFQ email (should be ignored)
```

---

## 9. Deployment Plan

### 9.1 Docker Service

**New Container: `horme-email-monitor`**

```dockerfile
# Dockerfile.email-monitor
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-email.txt .
RUN pip install --no-cache-dir -r requirements-email.txt

# Copy email monitoring service
COPY src/services/email_monitor.py .
COPY src/services/email_processor.py .

# Create attachments directory
RUN mkdir -p /app/email-attachments && chmod 700 /app/email-attachments

# Run as non-root user
RUN useradd -m emailmonitor
USER emailmonitor

CMD ["python", "-m", "src.services.email_monitor"]
```

**Docker Compose Integration**:
```yaml
services:
  email-monitor:
    build:
      context: .
      dockerfile: Dockerfile.email-monitor
    container_name: horme-email-monitor
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - EMAIL_IMAP_SERVER=${EMAIL_IMAP_SERVER}
      - EMAIL_USERNAME=${EMAIL_USERNAME}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data/email-attachments:/app/email-attachments
      - ./logs/email-monitor:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket"]
      interval: 60s
      timeout: 10s
      retries: 3
```

### 9.2 Database Migration

```bash
# Run migration script
docker exec horme-postgres psql -U horme_user -d horme_db -f /app/migrations/add_email_quotation_tables.sql

# Verify tables created
docker exec horme-postgres psql -U horme_user -d horme_db -c "\dt email_*"
```

### 9.3 Rollout Strategy

**Phase 1: Development (Week 1-2)**
- ✅ Implement email monitoring service
- ✅ Create database schema
- ✅ Develop API endpoints
- ✅ Unit tests complete

**Phase 2: Testing (Week 3)**
- ✅ Integration tests with mock IMAP server
- ✅ End-to-end testing with real emails
- ✅ Performance testing (100 emails/day simulation)

**Phase 3: Staging Deployment (Week 4)**
- ✅ Deploy to staging environment
- ✅ Monitor for 1 week with real email account
- ✅ User acceptance testing (UAT)

**Phase 4: Production Deployment (Week 5)**
- ✅ Deploy to production
- ✅ Monitor logs and error rates
- ✅ Gradual rollout (start with 1-hour polling, reduce to 5 minutes)

---

## 10. Monitoring & Operations

### 10.1 Logging Requirements

**Structured Logging Format**:
```json
{
  "timestamp": "2025-10-22T14:30:00Z",
  "service": "email-monitor",
  "level": "INFO",
  "message": "Email processed successfully",
  "email_id": "msg-12345",
  "sender": "customer@example.com",
  "attachments": 2,
  "processing_time_ms": 4500,
  "ai_confidence": 0.92
}
```

**Log Levels**:
- `DEBUG`: Email polling cycles, IMAP commands
- `INFO`: Email detected, processing started/completed
- `WARNING`: Attachment format not supported, low confidence score
- `ERROR`: Email fetch failed, processing error, AI API failure
- `CRITICAL`: IMAP connection permanently lost, database unreachable

### 10.2 Metrics & Alerts

**Key Metrics to Track**:
```python
# Prometheus metrics
email_monitor_polls_total
email_monitor_emails_detected_total
email_monitor_emails_processed_total
email_monitor_processing_errors_total
email_monitor_processing_duration_seconds
email_monitor_ai_confidence_score
```

**Alert Conditions**:
```
⚠️  Email fetch failures > 3 consecutive
⚠️  Processing error rate > 10%
⚠️  AI confidence score < 0.5 average
⚠️  No emails detected in 24 hours (possible connection issue)
⚠️  Disk usage > 80% (/app/email-attachments/)
```

---

## 11. Dependencies & Risks

### 11.1 Technical Dependencies

| Dependency | Purpose | Risk Level | Mitigation |
|------------|---------|------------|------------|
| imapclient | IMAP protocol | Low | Well-maintained library |
| Python email library | Email parsing | Low | Standard library |
| Existing DocumentProcessor | Attachment processing | Low | Already in production |
| OpenAI API | Requirement extraction | Medium | Use try-except, fallback to manual |
| PostgreSQL | Data storage | Low | Already in production |

### 11.2 Risk Assessment

**HIGH RISK**:
- ❌ **Webmail IMAP Access**: horme.com.sg webmail may not support IMAP protocol
  - **Mitigation**: Verify IMAP support with IT team before development
  - **Fallback**: Use Microsoft Graph API if Office 365, or Gmail API if Google Workspace

**MEDIUM RISK**:
- ⚠️ **Email Volume Spike**: Sudden increase in emails could overwhelm system
  - **Mitigation**: Implement rate limiting, queue-based processing

- ⚠️ **Attachment Size Limits**: Very large attachments (>50MB) may timeout
  - **Mitigation**: Set max file size limit (10MB), skip large files with notification

**LOW RISK**:
- ✅ **Duplicate Email Processing**: Same email processed multiple times
  - **Mitigation**: Message-ID uniqueness constraint in database

- ✅ **Non-RFQ Emails Flagged**: False positives in keyword detection
  - **Mitigation**: Manual review option, improve keyword list over time

---

## 12. Success Criteria & Acceptance

### 12.1 Acceptance Checklist

**Functionality**:
- [ ] Email monitoring service runs continuously without crashes
- [ ] RFQ emails detected with >90% accuracy
- [ ] Attachments downloaded and processed successfully
- [ ] Email body + attachments analyzed by AI
- [ ] Dashboard displays "New Quotation Requests" with correct data
- [ ] User can click request and trigger quotation flow
- [ ] Generated quotation links back to email request
- [ ] Duplicate emails prevented via Message-ID

**Performance**:
- [ ] Email polling cycle completes in <10 seconds
- [ ] AI processing completes in <60 seconds per email
- [ ] Dashboard loads in <2 seconds

**Security**:
- [ ] Email credentials stored in .env only (not in code)
- [ ] Attachments stored in secure directory (600 permissions)
- [ ] API endpoints require authentication
- [ ] No email content in logs (only metadata)

**Testing**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] End-to-end test with real email successful
- [ ] UAT sign-off from Sales Manager

**Documentation**:
- [ ] README updated with email monitoring setup
- [ ] API endpoints documented
- [ ] Environment variables documented
- [ ] Troubleshooting guide created

---

## 13. Future Enhancements (Post-V1)

**V1.1 - Email Response Automation**:
- Auto-reply to customer confirming receipt
- Send quotation PDF via email when generated
- Email template management

**V2.0 - Advanced Features**:
- Multi-inbox monitoring (multiple email accounts)
- Email threading/conversation tracking
- Machine learning for improved RFQ detection
- Customer auto-creation from email signatures
- Integration with CRM systems (Salesforce, HubSpot)

**V3.0 - Enterprise Features**:
- Multi-language support for international customers
- Custom email rules and workflows
- Email archival and search
- Analytics dashboard for email-to-quotation conversion rates

---

## Appendix A: Email Server Verification Checklist

Before implementation, verify the following with IT team:

```bash
# Test IMAP connectivity
telnet webmail.horme.com.sg 993

# Verify SSL certificate
openssl s_client -connect webmail.horme.com.sg:993

# Test authentication
# (Use imapclient Python library test script)
python test_imap_connection.py
```

**Questions for IT Team**:
1. Does webmail.horme.com.sg support IMAP protocol?
2. What is the IMAP server address and port?
3. Is SSL/TLS enabled?
4. Are there any IP restrictions or firewall rules?
5. What is the email retention policy?
6. Are there API alternatives (Exchange Web Services, Graph API)?

---

## Appendix B: Example Email Processing

**Sample RFQ Email**:
```
From: john.tan@marinacorp.com.sg
To: integrum@horme.com.sg
Subject: RFQ for Safety Equipment - Marina Project
Date: 2025-10-22 14:30:00

Dear Horme Team,

We require a quotation for the following safety equipment for our Marina Bay project:

1. Safety helmets (white) - 50 units
2. Safety glasses (clear lens, ANSI Z87.1) - 50 units
3. High-visibility vests (orange, size L) - 30 units
4. Safety gloves (cut-resistant, size 9) - 40 pairs

Please provide pricing and delivery timeline by end of week.

Best regards,
John Tan
Procurement Manager
Marina Corp Pte Ltd
john.tan@marinacorp.com.sg
+65 9123 4567

[Attachment: detailed_specifications.pdf]
```

**Expected Database Entry**:
```json
{
  "message_id": "<abc123@marinacorp.com.sg>",
  "sender_email": "john.tan@marinacorp.com.sg",
  "sender_name": "John Tan",
  "subject": "RFQ for Safety Equipment - Marina Project",
  "received_date": "2025-10-22T14:30:00Z",
  "has_attachments": true,
  "attachment_count": 1,
  "extracted_requirements": {
    "customer_name": "Marina Corp Pte Ltd",
    "project_name": "Marina Bay project",
    "contact_email": "john.tan@marinacorp.com.sg",
    "contact_phone": "+65 9123 4567",
    "items": [
      {
        "description": "Safety helmets (white)",
        "quantity": 50,
        "unit": "units",
        "specifications": ["white color"],
        "category": "safety"
      },
      {
        "description": "Safety glasses (clear lens, ANSI Z87.1)",
        "quantity": 50,
        "unit": "units",
        "specifications": ["clear lens", "ANSI Z87.1 certified"],
        "category": "safety"
      }
      // ... additional items
    ]
  },
  "ai_confidence_score": 0.94,
  "status": "completed"
}
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | System Analysis | Initial PRD creation |

**Approval Sign-Off**:
- [ ] Product Owner: ___________________  Date: _________
- [ ] Technical Lead: __________________  Date: _________
- [ ] Sales Manager: ___________________  Date: _________

---

**END OF PRD**
