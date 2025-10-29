# IMAP Troubleshooting Guide for integrum@horme.com.sg

## Current Status
- ✅ IMAP servers are reachable (mail.horme.com.sg, webmail.horme.com.sg)
- ✅ IMAP ports are open (993, 143)
- ✅ IMAP clients connect successfully
- ❌ Authentication fails with password: `integrum2@25`

## Problem
Password `integrum2@25` is rejected by IMAP servers, even though it may work for webmail login.

---

## Solution Path 1: Access cPanel to Get IMAP Settings

### Method A: Direct cPanel Access

1. **Try these cPanel URLs:**
   ```
   https://horme.com.sg:2083
   https://webmail.horme.com.sg:2083
   https://cpanel.horme.com.sg
   https://mail.horme.com.sg:2083
   ```

2. **Login with:**
   - Username: `integrum@horme.com.sg` OR just `integrum`
   - Password: `integrum2@25` (or your webmail password)

3. **Once in cPanel:**
   - Look for "Email" section
   - Click "Email Accounts"
   - Find `integrum@horme.com.sg`
   - Click "Connect Devices" or "Set Up Mail Client"
   - **Copy the exact IMAP settings shown**

### Method B: From Roundcube Webmail

1. **Look for cPanel link in Roundcube:**
   - Check top-right menu
   - Look for "Back to cPanel" or "Control Panel"
   - Or check bottom of page for cPanel link

2. **Alternative - Check Roundcube Settings:**
   - In Roundcube, click "Settings" (gear icon)
   - Look for "Server Settings" or "Account Info"
   - May show IMAP server details

---

## Solution Path 2: Enable IMAP Access

### Check if IMAP is Disabled

Many email providers require IMAP to be explicitly enabled:

1. **In cPanel → Email Accounts:**
   - Look for "Configure Mail Client" next to your email
   - Check if IMAP is listed as "Disabled"
   - If disabled, click "Enable IMAP Access"

2. **Alternative - Check for Access Control:**
   - Some servers require "Allow less secure apps" to be enabled
   - Check account security settings
   - May need to enable "IMAP/POP3 access"

---

## Solution Path 3: App-Specific Password

If your email account has 2FA or security features:

1. **Generate App-Specific Password:**
   - In cPanel or email settings
   - Look for "App Passwords" or "Application-Specific Passwords"
   - Generate new password for "Email Client" or "IMAP"
   - Use this password instead of your regular password

---

## Solution Path 4: Contact IT Admin

If you cannot access cPanel:

**Information to provide to Horme IT:**

```
Email Account: integrum@horme.com.sg
Issue: Need IMAP access for email monitoring system
Requirements:
  - IMAP server hostname
  - IMAP port (usually 993 for SSL)
  - IMAP username (usually full email address)
  - IMAP password (may be different from webmail password)
  - Confirm IMAP is enabled on the account

Purpose: Automated quotation request processing from customer emails
```

---

## Testing IMAP After Getting Credentials

### Quick Test (Command Line)

Once you have credentials, run this in Command Prompt:

```bash
cd C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov
python tests/utils/quick_imap_test.py integrum@horme.com.sg YOUR_PASSWORD
```

**Expected Success Output:**
```
✓ Connected to server
✓ Login successful!
✓ Found X folders
✓ INBOX has X messages
✓ SUCCESS! Use these settings:
```

### Update .env.production

After successful test, update the password:

1. Open: `.env.production`
2. Find line: `EMAIL_PASSWORD=integrum2@25`
3. Change to: `EMAIL_PASSWORD=YOUR_WORKING_PASSWORD`
4. Save file

### Full Validation Test

Run the complete IMAP test:

```bash
python tests/integration/test_imap_connection.py
```

**Should see:**
```
✓ Login successful
✓ INBOX selected
✓ Found messages
✓ IMAP CONNECTION TEST PASSED
```

---

## Common Scenarios and Solutions

### Scenario 1: Password Works in Webmail, Fails in IMAP

**Problem:** Webmail uses different authentication than IMAP

**Solution:**
- IMAP may be disabled → Enable in cPanel
- May require app-specific password → Generate in cPanel
- Security settings blocking IMAP → Check account security

### Scenario 2: Cannot Access cPanel

**Problem:** Don't have cPanel access credentials

**Solution:**
- Contact Horme IT admin
- Request IMAP credentials
- Ask them to enable IMAP on integrum@horme.com.sg

### Scenario 3: cPanel Shows Different Password

**Problem:** IMAP password different from webmail password

**Solution:**
- Use the password shown in cPanel "Configure Mail Client"
- Update `.env.production` with this password
- Re-test connection

### Scenario 4: Account Requires 2FA/MFA

**Problem:** Account has two-factor authentication enabled

**Solution:**
- Cannot use regular password for IMAP
- Must generate app-specific password
- Use app password in `.env.production`

---

## Verification Checklist

After getting credentials, verify:

- [ ] IMAP server hostname confirmed: `mail.horme.com.sg`
- [ ] IMAP port confirmed: `993`
- [ ] SSL/TLS enabled: `true`
- [ ] Username confirmed: `integrum@horme.com.sg`
- [ ] Password verified with quick test
- [ ] IMAP enabled on account
- [ ] Can access INBOX
- [ ] Can read messages
- [ ] Full integration test passes

---

## Next Steps After IMAP Works

Once IMAP authentication succeeds:

1. ✅ Mark Phase 2 as 100% complete
2. 🚀 Proceed to Phase 3: Frontend Validation
3. 🚀 Proceed to Phase 4: Integration Testing
4. 🚀 Start email monitoring service
5. 🚀 Test complete email-to-quotation flow

---

## Emergency Alternative: Skip Email Monitoring

If IMAP cannot be fixed immediately:

**The system can still work without email monitoring:**
- Use manual document upload via API
- Generate quotations from uploaded PDFs
- All other features work normally
- Come back to email monitoring later

**To skip and continue:**
- Mark IMAP as "deferred"
- Proceed with frontend validation
- Complete integration testing with manual uploads
- Deploy remaining features

---

## Support

**If still blocked after trying all solutions:**

Contact me with this information:
1. Which cPanel URLs you tried
2. Whether you can access cPanel
3. What error messages you see
4. Whether webmail password works
5. Whether you contacted IT admin

I can help adjust the deployment to work without email monitoring temporarily.
