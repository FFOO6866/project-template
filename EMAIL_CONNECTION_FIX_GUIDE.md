# Email Connection Fix Guide

## Issue Identified
The "Inbound Quotation Requests" page was showing only test data (integration-test@example.com) because the **email-monitor service was not running**.

## Root Cause
1. **Email-monitor service wasn't started** - Service was configured but not running
2. **Missing dependencies** - `requirements-email.txt` had `asyncpg` commented out
3. **Service crash loop** - Container kept restarting due to `ModuleNotFoundError: No module named 'asyncpg'`

## ✅ Solution Implemented

### Step 1: Fixed Dependencies ✅
Updated `requirements-email.txt` to include:
```txt
# Async PostgreSQL driver (required for database connections)
asyncpg>=0.29.0
structlog>=23.1.0
openai>=1.0.0
```

### Step 2: Rebuilding Service ✅ (In Progress)
```bash
docker-compose -f docker-compose.production.yml build --no-cache email-monitor
```

### Step 3: Start Service (Next)
```bash
docker-compose -f docker-compose.production.yml up -d email-monitor
```

## 📧 Email Configuration

Your email credentials are correctly configured in `.env.production`:

```bash
EMAIL_IMAP_SERVER=mail.horme.com.sg
EMAIL_IMAP_PORT=993
EMAIL_USERNAME=integrum@horme.com.sg
EMAIL_PASSWORD=Integrum2@25
EMAIL_USE_SSL=true
EMAIL_POLL_INTERVAL_SECONDS=300
```

## 🔍 How It Works

Once the email-monitor service is running:

1. **Connects to IMAP** server (`mail.horme.com.sg:993`)
2. **Polls inbox** every 5 minutes (300 seconds)
3. **Processes emails** with PDF/DOCX attachments
4. **Extracts RFQ data** using AI (OpenAI GPT-4)
5. **Creates quotation requests** in database
6. **Updates frontend** display with real email data

## 🧪 Testing

### Test Backend Directly
```bash
# Check email quotation requests
curl http://localhost:8002/api/email-quotation-requests/recent

# Should show:
# - Test data (integration-test@example.com) - CURRENT
# - Real emails from integrum@horme.com.sg - AFTER FIX
```

### Check Service Status
```bash
# Check if email-monitor is running
docker-compose -f docker-compose.production.yml ps email-monitor

# Should show:
# STATUS: Up (healthy)
# Not: Restarting
```

### View Email Monitor Logs
```bash
# Watch email processing in real-time
docker-compose -f docker-compose.production.yml logs -f email-monitor

# Look for:
# ✅ "Connected to IMAP server"
# ✅ "Processing email from..."
# ✅ "Created quotation request ID: X"
```

## 📊 Expected Behavior After Fix

### In Frontend (http://localhost:3010):
1. **"Inbound Quotation Requests"** page will show:
   - Test data (existing)
   - **NEW**: Real emails from integrum@horme.com.sg
2. Auto-refreshes every 60 seconds
3. Shows sender email, subject, status, confidence score

### In Backend:
- Email monitor runs continuously
- Checks inbox every 5 minutes
- Processes new emails automatically
- Stores in PostgreSQL database
- Real-time updates to frontend

## 🚨 If Still Showing Only Test Data

### Option 1: No Real Emails Yet
The inbox might be empty or emails might not match quotation request pattern.

**Check if inbox has emails**:
- Log into webmail: https://mail.horme.com.sg
- Username: integrum@horme.com.sg
- Password: Integrum2@25
- Look for emails with PDF/DOCX attachments

### Option 2: IMAP Connection Failed
**Check email-monitor logs**:
```bash
docker-compose -f docker-compose.production.yml logs email-monitor | grep -i error

# Common issues:
# - "Authentication failed" - Wrong password
# - "Connection refused" - Wrong server/port
# - "SSL error" - Certificate issues
```

**Test IMAP manually**:
```bash
# From within the container
docker exec horme-email-monitor python -c "
import imapclient
client = imapclient.IMAPClient('mail.horme.com.sg', port=993, ssl=True)
client.login('integrum@horme.com.sg', 'Integrum2@25')
print('✅ IMAP connection successful')
client.logout()
"
```

### Option 3: Email Processing Failed
**Check for processing errors**:
```bash
# Look for extraction failures
docker-compose -f docker-compose.production.yml logs email-monitor | grep -i "failed\|error"
```

## 🎯 Success Criteria

✅ **Email-monitor service running**: `docker ps` shows horme-email-monitor (healthy)
✅ **Connected to IMAP**: Logs show "Connected to IMAP server"
✅ **Processing emails**: Logs show "Processing email from..."
✅ **Database updated**: New rows in `email_quotation_requests` table
✅ **Frontend displays real data**: Inbound Quotation Requests shows real emails

## 📝 Troubleshooting Commands

```bash
# 1. Check service status
docker-compose -f docker-compose.production.yml ps email-monitor

# 2. View logs (last 50 lines)
docker-compose -f docker-compose.production.yml logs --tail=50 email-monitor

# 3. Watch logs live
docker-compose -f docker-compose.production.yml logs -f email-monitor

# 4. Check database for emails
docker exec horme-postgres psql -U horme_user -d horme_db -c "SELECT * FROM email_quotation_requests ORDER BY created_at DESC LIMIT 5;"

# 5. Restart service
docker-compose -f docker-compose.production.yml restart email-monitor

# 6. Force rebuild
docker-compose -f docker-compose.production.yml build --no-cache email-monitor
docker-compose -f docker-compose.production.yml up -d email-monitor
```

## 🔒 Security Notes

- Email credentials are in `.env.production` (not committed to git)
- Connection uses SSL/TLS (port 993)
- Password is stored securely as environment variable
- No plaintext credentials in code

---

**Status**: Rebuilding email-monitor with correct dependencies
**Next Step**: Start service and verify IMAP connection
**Expected Result**: Real emails from integrum@horme.com.sg appear in frontend
