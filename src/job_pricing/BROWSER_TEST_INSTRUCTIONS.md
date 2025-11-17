# Browser Testing Instructions - Week 1

**Objective**: Verify current end-to-end functionality through browser

---

## ✅ Pre-Test Checklist

Verify services are running:
```bash
# Check backend
curl http://localhost:8000/health
# Should return: {"status":"healthy"...}

# Check frontend
# Browser should open to: http://localhost:3000
```

**Both services should be running from your current session.**

---

## 🧪 Test 1: Form Submission (CRITICAL)

### Steps:
1. **Open Browser**: http://localhost:3000/job-pricing

2. **Fill Job Details Form**:
   ```
   Job Title:          Senior Data Scientist
   Location:           Singapore
   Portfolio:          TPC Group Corporate Office
   Department:         People & Organisation
   Employment Type:    Permanent
   Internal Grade:     10
   Job Family:         Total Rewards
   ```

3. **Click "Analyze Job Pricing" Button**

4. **Observe Behavior**:
   - Does loading spinner appear? ⏱️
   - Check browser console for errors (F12 → Console tab)
   - Does status change from "Analyzing..."?
   - Does results tab appear?

### Expected Results:
✅ **If Successful**:
- Form submits without errors
- Console shows API requests
- Results display after ~5 seconds
- TPC fields visible in results

❌ **If Failed**:
- CORS error in console → Need to fix CORS config
- Network error → Backend not accessible
- Timeout → API taking too long
- No results → Frontend/backend communication issue

### What to Report:
```
Test 1: Form Submission
Status: [✅ Pass / ❌ Fail]
Error Messages (if any):
- [Copy from browser console]

Screenshots:
- [Take screenshot of results page]

Network Tab:
- [Check XHR requests, copy request/response]
```

---

## 🧪 Test 2: Console Errors

### Steps:
1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Perform Test 1 again
4. Look for errors (red text)

### What to Look For:
```javascript
// ❌ Common Issues:
"CORS policy: No 'Access-Control-Allow-Origin'"
"Failed to fetch"
"NetworkError"
"TypeError: Cannot read property..."
"ValidationError"

// ✅ Should see:
"[API] Queued job processing task..."
"Request created successfully"
```

### What to Report:
```
Console Errors:
[Copy/paste any red error messages]
```

---

## 🧪 Test 3: Network Requests

### Steps:
1. Open DevTools (F12) → **Network** tab
2. Filter by **XHR** (XMLHttpRequest)
3. Perform Test 1
4. Check requests sent

### Expected Network Activity:
```
POST http://localhost:8000/api/v1/job-pricing/requests
→ Response: 201 Created, returns request ID

GET http://localhost:8000/api/v1/job-pricing/requests/{id}/status
→ Response: 200 OK, returns status (pending/processing/completed)

GET http://localhost:8000/api/v1/job-pricing/results/{id}
→ Response: 200 OK, returns full results with TPC fields
```

### What to Report:
```
Network Requests:
1. POST /requests: [Status code]
2. GET /status: [Status code]
3. GET /results: [Status code]

Request Payload (POST):
[Copy request body from Network tab]

Response Data (GET /results):
[Copy response body, especially TPC fields]
```

---

## 🧪 Test 4: Verify TPC Fields in Results

### Steps:
1. Complete Test 1 successfully
2. Scroll through results page
3. Look for TPC-specific data

### Where to Find TPC Fields:
```
Results should show:
- Portfolio: "TPC Group Corporate Office"
- Department: "People & Organisation"
- Employment Type: "Permanent"
- Job Family: "Total Rewards"
- Internal Grade: "10"
```

### What to Report:
```
TPC Fields in Results:
Portfolio: [Value shown]
Department: [Value shown]
Employment Type: [Value shown]
Job Family: [Value shown]
Internal Grade: [Value shown]

Missing Fields:
[List any fields not appearing]
```

---

## 🧪 Test 5: AI Buttons (Known to be Mocked)

**Purpose**: Confirm these are still mocked (we'll fix in Week 2-3)

### Test Each Button:

#### 1. "AI Generate Skills" Button
- Click button
- **Expected**: Spinner for ~1.5 sec, then hardcoded skills appear
- **Status**: 🔴 MOCKED (this is OK for now)

#### 2. "AI Generate Job Scope" Button
- Click button
- **Expected**: Spinner for ~2 sec, then fake description
- **Status**: 🔴 MOCKED (this is OK for now)

#### 3. "AI Map to Mercer" Button
- Click button
- **Expected**: Spinner for ~2 sec, then fake Mercer code
- **Status**: 🔴 MOCKED (this is OK for now)

#### 4. "AI Generate Alternatives" Button
- Click button
- **Expected**: Spinner for ~1.5 sec, then fake titles
- **Status**: 🔴 MOCKED (this is OK for now)

### What to Report:
```
AI Buttons Status:
All buttons show mocked behavior: [✅ Confirmed]
Any unexpected errors: [None / List errors]
```

---

## 🧪 Test 6: Benchmarking Tab (Known Fake Data)

### Steps:
1. Complete Test 1
2. Click "Benchmarking" tab
3. Observe market data

### Expected:
- Shows MyCareersFuture listings (hardcoded)
- Shows Glassdoor comparisons (hardcoded)
- Shows Mercer benchmarks (hardcoded)

### What to Report:
```
Benchmarking Tab:
Data displays: [✅ Yes / ❌ No]
Data is fake: [✅ Confirmed]
Any UI issues: [None / List issues]
```

---

## 🧪 Test 7: Validation (NEW - Just Added)

### Test Invalid Employment Type:
1. Fill form with:
   ```
   Job Title: Test
   Employment Type: INVALID_TYPE
   ```
2. Click "Analyze Job Pricing"
3. **Expected**: Error message displays

### Test Too Many Skills:
1. Try adding 51+ skills
2. **Expected**: Validation error

### What to Report:
```
Validation Tests:
Invalid employment_type: [✅ Shows error / ❌ Accepted]
Error message clear: [✅ Yes / ❌ No]
```

---

## 📊 Summary Report Template

After completing all tests, fill this out:

```markdown
# Browser Test Results - Week 1

**Date**: 2025-11-12
**Tester**: [Your name]

## Overall Status
[ ] All tests passed
[ ] Some tests failed (details below)
[ ] Critical blocker found

## Test Results

### Test 1: Form Submission
Status: [✅ Pass / ❌ Fail]
Notes: [Your observations]

### Test 2: Console Errors
Errors Found: [None / List errors]

### Test 3: Network Requests
All requests succeeded: [✅ Yes / ❌ No]
Status codes: [200, 201, etc.]

### Test 4: TPC Fields in Results
All fields displayed: [✅ Yes / ❌ No]
Missing fields: [None / List]

### Test 5: AI Buttons (Mocked)
All buttons mocked: [✅ Confirmed]

### Test 6: Benchmarking Tab
Displays fake data: [✅ Confirmed]

### Test 7: Validation
Validation works: [✅ Yes / ❌ No]

## Screenshots
[Attach screenshots of:]
1. Form filled out
2. Results page
3. Any errors
4. Browser console

## Next Steps
Based on test results:
- [ ] Proceed to Week 2 (remove mocks)
- [ ] Fix blocking issues first
- [ ] Investigate [specific issue]

## Questions/Concerns
[List any questions or concerns]
```

---

## 🚨 If You Find Critical Issues

**Stop and report if**:
- Form doesn't submit at all
- CORS errors prevent API calls
- Backend returns 500 errors
- Frontend crashes
- No results ever appear

**How to Debug**:
```bash
# Check backend logs
cd C:\Users\fujif\OneDrive\Documents\GitHub\rrrr\src\job_pricing
docker-compose logs api --tail=50

# Check Celery worker logs
docker-compose logs celery-worker --tail=50

# Restart services if needed
docker-compose restart
```

---

## ✅ Success Criteria

**Test 1 passes = ✅ Ready for Week 2**
- Form submits successfully
- Results display
- TPC fields flow through
- Known mocks are confirmed

**This proves the foundation works, then we can enhance it.**

---

**Next After Testing**: Report results, then we'll systematically remove mocks and fix backend processing per the 6-8 week plan.
