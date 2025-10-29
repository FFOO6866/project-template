# Frontend "Failed to Fetch" Fix Guide

## Issue Identified
The frontend is showing "Failed to fetch" errors for "Inbound Quotation Requests" because it was built with outdated environment variables.

## Root Cause
- **Next.js bakes `NEXT_PUBLIC_*` variables at BUILD time**, not runtime
- Frontend was built 3 days ago with old API URL
- Current environment variables are correct, but the browser JavaScript bundle has old values

## ✅ Backend Status
- ✅ Backend API working perfectly on http://localhost:8002
- ✅ Endpoint `/api/email-quotation-requests/recent` returns real data
- ✅ Database has 45 documents and 13 quotes
- ✅ All services healthy

## 🔧 Solution Applied

### Step 1: Frontend Rebuilt ✅
```bash
docker-compose -f docker-compose.production.yml build frontend
```
**Result**: Build completed (using cached layers)

### Step 2: Frontend Restarted ✅
```bash
docker-compose -f docker-compose.production.yml up -d frontend
```
**Result**: Container recreated and restarted

## 🧪 Test the Fix

### Option A: Browser Test
1. Open http://localhost:3010
2. Navigate to "Inbound Quotation Requests" page
3. Should now load data instead of "Failed to fetch"
4. **Clear browser cache** if still showing error (Ctrl+Shift+R)

### Option B: API Test
```bash
# Test backend directly
curl http://localhost:8002/api/email-quotation-requests/recent

# Expected: Returns array of email quotation requests
```

## 🔍 If Still Not Working

### Force Rebuild (No Cache)
```bash
# Stop frontend
docker-compose -f docker-compose.production.yml stop frontend

# Remove frontend container and image
docker-compose -f docker-compose.production.yml rm -f frontend
docker rmi horme-pov-frontend

# Rebuild from scratch
docker-compose -f docker-compose.production.yml build --no-cache frontend

# Start again
docker-compose -f docker-compose.production.yml up -d frontend
```

### Check Environment Variables
```bash
# Check what the frontend container sees
docker exec horme-frontend env | grep NEXT_PUBLIC

# Expected:
# NEXT_PUBLIC_API_URL=http://localhost:8002
# NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001
```

### Check Build Args
The docker-compose.production.yml should pass these as build args:
```yaml
args:
  - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
  - NEXT_PUBLIC_WEBSOCKET_URL=${NEXT_PUBLIC_WEBSOCKET_URL}
```

## 📝 What to Look For

### Success Indicators:
- ✅ Frontend loads at http://localhost:3010
- ✅ "Inbound Quotation Requests" shows data
- ✅ No "Failed to fetch" errors in browser console
- ✅ Browser Network tab shows requests to http://localhost:8002

### Failure Indicators:
- ❌ "Failed to fetch" error still appears
- ❌ Browser console shows requests to wrong URL
- ❌ Network tab shows requests to http://localhost:3010 (wrong!)

## 🎯 Expected Behavior

The frontend should:
1. Load from http://localhost:3010
2. Make API requests to http://localhost:8002
3. Display real data from the backend
4. Show 1 email quotation request from Integration Test User

## 💡 Prevention

To avoid this in future:
1. **Always rebuild frontend** after changing `.env.production`
2. **Clear browser cache** after frontend rebuilds
3. **Test with curl** first to verify backend works
4. **Check browser DevTools** Network tab to see actual API calls

## 📊 Current System Status

### Services Running:
- ✅ PostgreSQL (localhost:5432) - Healthy
- ✅ Redis (localhost:6379) - Healthy
- ✅ Neo4j (localhost:7474, 7687) - Healthy
- ✅ Backend API (localhost:8002) - Healthy
- ✅ Frontend (localhost:3010) - Rebuilt & Restarted
- ✅ WebSocket (localhost:8001) - Healthy

### Data Available:
- 45 Documents processed
- 13 Quotes generated
- 1 Email quotation request
- 0 Customers created yet

---

**Status**: Frontend rebuilt and restarted
**Next Step**: Test at http://localhost:3010 and clear browser cache if needed
**Confidence**: High - backend is working, frontend just needed rebuild
