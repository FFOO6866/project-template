# Phase 4: Integration Testing Guide
**Email-to-Quotation Complete Flow Test**

## Overview

We will test the complete email quotation flow:
1. Send test email → integrum@horme.com.sg
2. Verify email appears in IMAP inbox
3. Manually insert email into database (simulating monitor)
4. Trigger processing via API
5. Verify quotation generation
6. Check frontend display

---

## Prerequisites ✅

All met:
- ✅ PostgreSQL running (port 5434)
- ✅ Redis running (port 6381)
- ✅ API service running (port 8002)
- ✅ Database tables created (email_quotation_requests, email_attachments)
- ✅ IMAP credentials working (mail.horme.com.sg, Integrum2@25)
- ✅ Frontend built successfully

---

## Test Steps

### Step 1: Send Test Email

**Action:** Send email from your personal email account

**To:** integrum@horme.com.sg

**Subject:** Request for Quotation - Integration Test

**Body:**
```
Hello,

We need the following items for our construction project:

1. 50 safety helmets (hard hats)
2. 100 pairs of safety gloves
3. 25 high-visibility safety vests
4. 10 safety harnesses for working at height

Please provide a quotation with pricing and delivery timeline.

Thank you,
[Your Name]
```

**Expected:** Email sent successfully

---

### Step 2: Verify Email in IMAP

Run IMAP test to confirm email arrived:

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov
python tests/integration/test_imap_connection.py
```

**Expected Output:**
```
✓ INBOX has X messages (should be 8 or more)
✓ Found N messages with RFQ keywords
```

**Verify:** Your test email appears in the inbox

---

### Step 3: Manually Create Email Record

Since email monitor isn't running, we'll manually insert the email record.

**Option A: Use Python Script** (Recommended)

Create and run: `tests/utils/insert_test_email.py`

```python
import asyncio
import asyncpg
import os
from datetime import datetime

async def insert_test_email():
    DATABASE_URL = "postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5434/horme_db"

    conn = await asyncpg.connect(DATABASE_URL)

    # Insert test email
    email_id = await conn.fetchval("""
        INSERT INTO email_quotation_requests (
            message_id,
            sender_email,
            sender_name,
            subject,
            received_date,
            body_text,
            status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7
        ) RETURNING id
    """,
        f"test-{datetime.now().timestamp()}@test.com",  # Unique message_id
        "test@example.com",  # Your email
        "Test User",
        "Request for Quotation - Integration Test",
        datetime.now(),
        """Hello,

We need the following items for our construction project:

1. 50 safety helmets (hard hats)
2. 100 pairs of safety gloves
3. 25 high-visibility safety vests
4. 10 safety harnesses for working at height

Please provide a quotation with pricing and delivery timeline.

Thank you""",
        "pending"
    )

    print(f"✓ Inserted test email with ID: {email_id}")
    await conn.close()
    return email_id

if __name__ == "__main__":
    email_id = asyncio.run(insert_test_email())
    print(f"\nNext step: Process email {email_id}")
    print(f"curl -X POST http://localhost:8002/api/email-quotation-requests/{email_id}/process")
```

**Run:**
```bash
python tests/utils/insert_test_email.py
```

**Expected:** Email ID returned (e.g., 1, 2, 3...)

---

### Step 4: Trigger Processing via API

Use the email ID from Step 3:

```bash
# Replace {email_id} with actual ID from Step 3
curl -X POST http://localhost:8002/api/email-quotation-requests/{email_id}/process
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Processing started",
  "request_id": {email_id}
}
```

---

### Step 5: Check Processing Status

Wait 30-60 seconds, then check status:

```bash
curl http://localhost:8002/api/email-quotation-requests/{email_id}
```

**Expected Response:**
```json
{
  "id": {email_id},
  "status": "completed",
  "extracted_requirements": { ... },
  "ai_confidence_score": 0.85,
  "quotation_id": 123,
  ...
}
```

**Key Fields to Check:**
- `status`: Should be "completed" (not "failed" or "pending")
- `extracted_requirements`: Should have product requirements extracted
- `ai_confidence_score`: Should be > 0.7
- `quotation_id`: Should have a quotation ID (not null)

---

### Step 6: Verify Quotation Created

Use quotation_id from Step 5:

```bash
curl http://localhost:8002/api/quotations/{quotation_id}
```

**Expected Response:**
```json
{
  "id": {quotation_id},
  "quote_number": "Q-2025-XXXX",
  "status": "draft",
  "total_amount": "XXX.XX",
  "items": [
    {
      "product_name": "Safety Helmet...",
      "quantity": 50,
      "unit_price": "XX.XX",
      "line_total": "XXX.XX"
    },
    ...
  ]
}
```

**Key Checks:**
- Items array has 4 products (helmets, gloves, vests, harnesses)
- Quantities match request (50, 100, 25, 10)
- Prices are real (not 0 or mock values)
- Total amount calculated correctly

---

### Step 7: Check Database Directly

Verify data in database:

```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT
    id,
    sender_email,
    subject,
    status,
    quotation_id,
    ai_confidence_score
FROM email_quotation_requests
WHERE id = {email_id};
"
```

**Expected:**
```
 id | sender_email      | subject                  | status    | quotation_id | ai_confidence_score
----+-------------------+--------------------------+-----------+--------------+--------------------
  X | test@example.com  | Request for Quotation... | completed |          123 |                0.85
```

---

### Step 8: Frontend Verification (Optional)

1. Open browser: http://localhost:3010 (or wherever frontend is running)
2. Look for "New Quotation Requests" section
3. Find your test email request
4. Click to view details
5. Click "View Quotation" button
6. Verify quotation displays with correct items

---

## Success Criteria

### ✅ Complete Success
All of these must pass:

- [ ] Test email sent successfully
- [ ] Email appears in IMAP inbox
- [ ] Email record inserted in database
- [ ] API processing triggered successfully
- [ ] Status changes to "completed" (not "failed")
- [ ] AI extracted requirements with confidence > 0.7
- [ ] Quotation created with correct items
- [ ] All 4 product types matched
- [ ] Quantities correct (50, 100, 25, 10)
- [ ] Prices are real (not mock/zero)
- [ ] Total calculated correctly
- [ ] Database record correct
- [ ] (Optional) Frontend displays correctly

### ⚠️ Partial Success
If any of these fail, we need to debug:

- API returns error → Check logs: `docker logs horme-api`
- Status stays "pending" → OpenAI API may be slow
- Status becomes "failed" → Check error_message in database
- No quotation created → ProductMatcher may not find products
- Wrong quantities → AI extraction issue
- Mock prices → Database has no real product prices

---

## Troubleshooting

### Issue: API Processing Fails

**Check API logs:**
```bash
docker logs horme-api --tail=100
```

**Look for:**
- OpenAI API errors
- Database connection errors
- Missing environment variables

### Issue: AI Extraction Low Confidence

**Check extracted_requirements:**
```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT extracted_requirements
FROM email_quotation_requests
WHERE id = {email_id};
"
```

**If requirements look wrong:**
- Email body may be too short/unclear
- Try more specific product names
- Add quantities explicitly

### Issue: No Products Matched

**Check if products exist in database:**
```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT name, category
FROM products
WHERE name ILIKE '%helmet%'
   OR name ILIKE '%glove%'
   OR name ILIKE '%vest%'
   OR name ILIKE '%harness%'
LIMIT 10;
"
```

**If no products found:**
- Database may need product data loaded
- Run product import script first
- Use different product names that exist in DB

### Issue: Quotation Has Zero Prices

**Check product prices:**
```bash
docker exec horme-postgres psql -U horme_user -d horme_db -c "
SELECT name, list_price
FROM products
WHERE name ILIKE '%helmet%'
LIMIT 5;
"
```

**If prices are NULL/0:**
- Product data incomplete
- Need to load pricing data
- This is expected if using sample data

---

## Next Steps After Testing

### If All Tests Pass ✅

1. **Enable Email Monitor Service**
   - Create Docker service for EmailMonitor
   - Configure to run every 5 minutes
   - Test automatic email detection

2. **Production Deployment**
   - Deploy to production environment
   - Configure production email credentials
   - Enable monitoring and alerting

3. **User Acceptance Testing**
   - Have real users send test emails
   - Verify end-to-end flow works
   - Collect feedback

### If Tests Fail ❌

1. **Review Logs**
   - Check all error messages
   - Identify failure point
   - Document exact error

2. **Fix Issues**
   - Apply proper fixes (no shortcuts)
   - Re-test after each fix
   - Verify fix doesn't break other components

3. **Re-run Tests**
   - Start from Step 1 again
   - Verify all steps pass
   - Document any remaining issues

---

## Clean Up After Testing

```bash
# Delete test email record
docker exec horme-postgres psql -U horme_user -d horme_db -c "
DELETE FROM email_quotation_requests
WHERE sender_email = 'test@example.com';
"

# Or keep it for reference but mark as test
docker exec horme-postgres psql -U horme_user -d horme_db -c "
UPDATE email_quotation_requests
SET processing_notes = 'TEST RECORD - Integration Testing'
WHERE sender_email = 'test@example.com';
"
```

---

## Report Template

After testing, document results:

```markdown
# Integration Test Results

**Date:** 2025-10-22
**Tester:** [Your Name]
**Email ID:** {email_id}
**Quotation ID:** {quotation_id}

## Results

- [ ] Email sent successfully
- [ ] IMAP detection: PASS/FAIL
- [ ] Database insertion: PASS/FAIL
- [ ] API processing: PASS/FAIL
- [ ] AI extraction: PASS/FAIL (confidence: X.XX)
- [ ] Product matching: PASS/FAIL (X/4 products)
- [ ] Quotation creation: PASS/FAIL
- [ ] Pricing correct: PASS/FAIL
- [ ] Frontend display: PASS/FAIL

## Issues Found

1. [Issue description]
   - Severity: Critical/High/Medium/Low
   - Fix applied: Yes/No
   - Status: Fixed/In Progress/Blocked

## Screenshots

[Attach screenshots of:]
- API response
- Database query results
- Frontend display (if applicable)

## Recommendations

[Next steps based on test results]
```

---

**Ready to start testing!** Follow the steps above and document all results.
