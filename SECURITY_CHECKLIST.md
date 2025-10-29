# Security Checklist - IMMEDIATE ACTIONS REQUIRED

**Status**: 🔴 ACTION REQUIRED
**Priority**: CRITICAL

---

## ✅ What I've Done (Automated)

1. ✅ **Removed exposed API key** from `.env.production`
2. ✅ **Added security warning** with clear instructions
3. ✅ **Added .env.production to .gitignore** (prevents accidental commits)
4. ✅ **Configured CORS** for local Docker testing

---

## 🚨 What YOU Must Do NOW (Manual Steps)

### Step 1: Revoke the Exposed Key (CRITICAL - Do This First!)

```
1. Open browser: https://platform.openai.com/api-keys
2. Login to your OpenAI account
3. Find the key starting with: sk-proj-brP97Iq3Rw0O29...
4. Click the "Revoke" or trash icon next to it
5. Confirm revocation
```

**Why**: The exposed key can be used by anyone who saw the chat conversation. Revoke it immediately to prevent unauthorized charges.

---

### Step 2: Generate a NEW API Key

```
1. Still at: https://platform.openai.com/api-keys
2. Click: "Create new secret key"
3. Name it: "Horme POV Production"
4. Optional: Set permissions to "Restricted" and limit to specific models
5. Click: "Create secret key"
6. COPY THE KEY NOW (you won't see it again!)
   - It will look like: sk-proj-NEW_KEY_HERE...
```

---

### Step 3: Set Budget Limits (Highly Recommended)

```
1. Go to: https://platform.openai.com/account/billing/limits
2. Set hard limit: $100/month (or your preferred amount)
3. Set email alerts:
   - Alert at $25
   - Alert at $50
   - Alert at $75
4. Save settings
```

**Why**: Prevents surprise bills if the key is misused or your app makes more calls than expected.

---

### Step 4: Update .env.production with NEW Key

```bash
# Open .env.production in your text editor
# Find this line (around line 86):
OPENAI_API_KEY=PASTE_YOUR_NEW_KEY_HERE

# Replace with your NEW key:
OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY_HERE

# Save the file
```

**IMPORTANT**:
- Do NOT share this file
- Do NOT commit it to git (already in .gitignore)
- Do NOT paste the key in chat/email

---

### Step 5: Verify Configuration

```bash
# Check .env.production is NOT tracked by git
git status .env.production

# Expected output: "nothing to commit" or file not listed
# If you see "Changes to be committed", DO NOT COMMIT!
```

---

## 📋 Current .env.production Status

### ✅ CONFIGURED (Ready to Use)
- Database credentials (PostgreSQL)
- Redis credentials
- Neo4j credentials
- Security keys (SECRET_KEY, JWT_SECRET, ADMIN_PASSWORD)
- Hybrid recommendation weights
- Web scraping settings
- CORS origins (configured for local Docker)

### ⚠️ NEEDS YOUR ACTION
- **OPENAI_API_KEY** → Paste your NEW key here
  - File: `.env.production`
  - Line: 86
  - Current value: `PASTE_YOUR_NEW_KEY_HERE`

---

## 🔐 Password Summary (Already Generated)

Your `.env.production` already has these secure passwords:

```bash
# Database
POSTGRES_PASSWORD=2b63586bf11e28434f192c20cebbee4373fc66d82364527a

# Redis
REDIS_PASSWORD=06ff793b4cda9ae630a12847f884d66315c4e3971308b1bf

# Neo4j
NEO4J_PASSWORD=d8b90dac8a997fb686e0607e34aaf203ea7a7a4615412986

# Application Security
SECRET_KEY=81bb1bb54384f5f4c13bff2a77b96028febfc4fa460fd98dbd8543a7599fea8d
JWT_SECRET=4389a12410f6b68ee06e9666d79421de268a8bf126012bf643b478432f635a95
ADMIN_PASSWORD=d95c9e4b7d917ab8abd6086502b5d3556be3d1a06b38a9d4d3fd55d5d4503cf5
```

**Action**: ✅ No change needed - these are already secure

---

## 🚀 After You Update the OpenAI Key

Once you've completed Steps 1-4 above, you can proceed with deployment:

```bash
# 1. Start Docker services
docker-compose -f docker-compose.production.yml up -d

# 2. Load product data (19,143 products)
docker exec horme-api python scripts/load_horme_products.py

# 3. Enrich products with web scraping (9,764 products)
docker exec horme-enrichment-worker python scripts/scrape_horme_product_details.py

# 4. Test API
curl http://localhost:8002/health
```

---

## 🔒 Security Best Practices Going Forward

### DO ✅
- Store API keys in `.env.production` (local file only)
- Revoke keys immediately if exposed
- Rotate keys every 90 days
- Set budget limits in OpenAI dashboard
- Use environment variables (`os.getenv()`) in code
- Keep `.env.production` in `.gitignore`

### DON'T ❌
- Share API keys in chat/email/Slack
- Commit `.env.production` to git
- Hardcode keys in source code
- Include keys in screenshots
- Use the same key across multiple projects
- Share your `.env.production` file

---

## 📊 Verification Checklist

Before proceeding with deployment, verify:

- [ ] Old API key REVOKED in OpenAI dashboard
- [ ] NEW API key generated in OpenAI dashboard
- [ ] Budget limits set ($100/month recommended)
- [ ] NEW key pasted in `.env.production` (line 86)
- [ ] `.env.production` saved
- [ ] `git status .env.production` shows file is ignored
- [ ] You have NOT committed `.env.production` to git
- [ ] You have NOT shared the new key anywhere

---

## 🆘 If You're Unsure

If you need to verify your `.env.production` is correct:

```bash
# Check if OpenAI key is set (should NOT show "PASTE_YOUR_NEW_KEY_HERE")
grep "OPENAI_API_KEY" .env.production

# Expected output: OPENAI_API_KEY=sk-proj-... (your actual key)
# Bad output: OPENAI_API_KEY=PASTE_YOUR_NEW_KEY_HERE (still needs updating)
```

---

## 📞 Next Steps

1. ✅ Complete Steps 1-4 above (revoke old key, generate new key, update .env.production)
2. ✅ Verify checklist items
3. ✅ Proceed to deployment (follow `DEPLOYMENT_GUIDE.md`)

---

**Current Status**: Waiting for you to update OPENAI_API_KEY in `.env.production`

**Time Required**: 5-10 minutes

**After Completion**: You can safely proceed with deployment
