# ROOT CAUSE ANALYSIS: Document Extraction Failures

## Problem Statement

User reports recurring failures where the AI chat cannot extract requirements from uploaded documents:

**Example 1 (PDF)**:
```
"RFQ_RFQ_202510_1213_Waterfront_Resort_Procurement.pdf"
AI Response: "Couldn't pull anything specific from the PDF."
```

**Example 2 (DOCX)**:
```
"RFQ_RFQ_202510_1257_Airways_Engineering_Company.docx"
AI Response: "Couldn't pull anything specific from the DOCX. The format might be unusual or it's mostly text without clear product lists."
```

## Symptoms

1. **Error Message Location**: `frontend/components/chat-interface.tsx:123`
2. **Trigger Condition**: `extractedData.requirements.items.length === 0`
3. **Status Pattern**: Document status shows `completed` but no items extracted
4. **Recurring Pattern**: Problem happens "again and again after claimed fixing"

## Investigation Findings

### 1. Architecture Discovery

**CRITICAL FINDING**: Multiple backend services with different purposes:

```
Port 8000: src/core/api.py           → Not used by frontend (my created endpoints)
Port 8001: src/websocket/chat_server.py  → WebSocket chat (not HTTP)
Port 8002: src/nexus_backend_api.py  → ACTUAL backend used by frontend ✅
```

**Frontend Calls**:
```typescript
// Line 81: Frontend polls THIS endpoint
const response = await fetch(`http://localhost:8002/api/documents/${documentId}`)

// Line 202: Frontend sends chat messages to THIS endpoint
const response = await fetch('http://localhost:8002/api/chat', {...})
```

### 2. Actual Document Processing Flow

From `src/nexus_backend_api.py`:

```
1. POST /api/files/upload (line 1004)
   ↓
2. Create document record with ai_status='pending' (line 1034)
   ↓
3. Start background task: process_document_pipeline() (line 1051)
   ↓
4. DocumentProcessor().process_document() (line 426)
   ↓
5. Update database with ai_extracted_data (line 521)
   ↓
6. Frontend polls GET /api/documents/{id} (line 982)
   ↓
7. Frontend checks: extractedData.requirements.items.length (line 97)
```

### 3. Document Processor Capabilities

**Current Processor** (`src/services/document_processor.py`):

✅ **DOCX Extraction** (line 263-302):
- Extracts paragraphs
- **Extracts tables** with HEADERS and ROW markers
- Uses python-docx library

✅ **PDF Extraction** (line 166-261):
- Strategy 1: Camelot (best for tables)
- Strategy 2: PDFPlumber (text + tables)
- Strategy 3: PyPDF2 (fallback)

✅ **OpenAI Analysis** (line 414-507):
- Sends extracted text to GPT-4
- Detailed prompts for table/list/text extraction
- Returns structured JSON with items[]

## ROOT CAUSES IDENTIFIED

### Primary Root Cause: **Misdiagnosed Problem**

**I was fixing the WRONG system!**

1. **Created solutions for `src/core/api.py` (port 8000)**
   - But frontend uses `src/nexus_backend_api.py` (port 8002)

2. **Created `src/api/document_api.py`**
   - But this was never imported or used
   - Frontend doesn't know about these endpoints

3. **Enhanced `src/websocket/chat_server.py`**
   - But chat server isn't involved in document processing
   - It's purely for real-time chat conversations

### Secondary Root Causes

#### RC-1: **No Systematic Investigation**
- Never checked which backend service the frontend actually uses
- Never traced the actual API calls from frontend code
- Never verified port numbers against actual deployment

#### RC-2: **Incorrect Assumptions**
- Assumed `/api/v1/...` structure without checking frontend
- Assumed main API (port 8000) is what frontend uses
- Assumed the problem was "PDF not supported" without evidence

#### RC-3: **No Debugging at Failure Point**
- Never checked actual OpenAI API responses
- Never examined extracted text from failing documents
- Never tested with actual failure case documents

#### RC-4: **Integration Blindspot**
- Created EnhancedDocumentProcessor but never integrated it
- Added document API routes but to wrong FastAPI app
- Modified chat server but it's not in the processing pipeline

## Actual Problem (Hypothesis)

Based on code review, the **REAL** issues are likely:

### Issue 1: OpenAI Extraction Quality

The `DocumentProcessor._analyze_requirements()` function:
- Only sends **first 8000 characters** to OpenAI (line 423)
- If tables are at end of document → missed
- If document has lots of preamble → items get truncated

### Issue 2: Text Extraction Edge Cases

For DOCX files specifically:
- Merged cells might cause issues (line 285-288)
- Complex table formatting might not extract cleanly
- Tables within tables might be skipped

### Issue 3: OpenAI API Failures (Unhandled)

```python
# Line 505: If OpenAI fails, error is logged but...
except Exception as e:
    logger.error(f"OpenAI API error: {str(e)}")
    raise RuntimeError(f"AI requirement extraction failed: {str(e)}")
```

- If OpenAI API key is invalid/expired → fails
- If OpenAI rate limit hit → fails
- If OpenAI service down → fails
- Error gets logged but frontend just shows "Couldn't pull anything specific"

### Issue 4: Database Schema Mismatch

`src/nexus_backend_api.py` expects:
```sql
ai_extracted_data JSONB  -- Stores full extraction result
```

But `src/services/document_processor.py` stores (line 522):
```python
json.dumps(extracted_data)  # Where extracted_data = { 'requirements': {...}, 'processor_version': '1.1.0', ... }
```

Frontend expects (line 97):
```typescript
extractedData.requirements.items  // Direct access
```

This should work IF the database stores it correctly!

## Why "Fixing" Hasn't Worked

### Fix Attempt 1: Created New Document API
- **Outcome**: Created `src/api/document_api.py` with enhanced processing
- **Why it failed**: Frontend doesn't call this API (wrong service, wrong port)

### Fix Attempt 2: Enhanced Chat Server
- **Outcome**: Added document data loading to websocket chat
- **Why it failed**: Chat server is not in the document processing pipeline

### Fix Attempt 3: Multi-Strategy Processor
- **Outcome**: Created `EnhancedDocumentProcessor` with Vision, Docling, etc.
- **Why it failed**: Never integrated into `nexus_backend_api.py`

## Systemic Issues

### Issue A: **No Testing Against Real Failures**

Every "fix" was theoretical:
- Never tested with `RFQ_RFQ_202510_1213_Waterfront_Resort_Procurement.pdf`
- Never tested with `RFQ_RFQ_202510_1257_Airways_Engineering_Company.docx`
- Never checked if extraction actually succeeds after changes

### Issue B: **No Validation of Deployment**

After each fix:
- Never verified which service is actually running
- Never checked if new code is actually deployed
- Never tested frontend → backend → database flow

### Issue C: **Architecture Knowledge Gap**

Didn't know:
- There are 3 different backend services
- Frontend uses port 8002 specifically
- `nexus_backend_api.py` is the production backend

## Evidence-Based Next Steps

### Step 1: **Verify Current State**

```bash
# Check what's actually running
netstat -ano | findstr "8000 8001 8002"

# Check which services are deployed
docker ps

# Test actual endpoint frontend uses
curl http://localhost:8002/api/documents/1
```

### Step 2: **Test with Actual Failure Cases**

```bash
# Upload the problematic documents
curl -X POST http://localhost:8002/api/files/upload \
  -F "file=@RFQ_RFQ_202510_1213_Waterfront_Resort_Procurement.pdf" \
  -F "document_type=rfp"

# Check extraction result
curl http://localhost:8002/api/documents/1

# Check database directly
psql -U horme_user -d horme_db -c "SELECT id, ai_status, ai_extracted_data FROM documents WHERE id = 1;"
```

### Step 3: **Add Debugging to Actual Pipeline**

Modify `src/services/document_processor.py`:

```python
async def _extract_text(self, file_path: str) -> tuple[str, str]:
    """Extract text with debug logging"""
    text, method = ... # existing code

    # DEBUG: Log extracted text
    logger.info(f"Extracted {len(text)} chars using {method}")
    logger.info(f"First 500 chars: {text[:500]}")
    logger.info(f"Last 500 chars: {text[-500:]}")

    return text, method

async def _analyze_requirements(self, text: str) -> Dict[str, Any]:
    """Analyze with debug logging"""

    # DEBUG: Log prompt sent to OpenAI
    logger.info(f"Sending {len(text)} chars to OpenAI (truncated to {min(len(text), 8000)})")

    response = await self.openai_client.chat.completions.create(...)

    # DEBUG: Log OpenAI response
    logger.info(f"OpenAI response: {response.choices[0].message.content[:1000]}")

    requirements = json.loads(requirements_json)

    # DEBUG: Log extraction result
    logger.info(f"Extracted requirements: {json.dumps(requirements, indent=2)}")

    return requirements
```

### Step 4: **Check OpenAI Configuration**

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test OpenAI API directly
python -c "
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model='gpt-4-turbo-preview',
    messages=[{'role': 'user', 'content': 'Test'}]
)
print(response.choices[0].message.content)
"
```

### Step 5: **Fix the Right Service**

If the issue IS in extraction quality, modify **`src/nexus_backend_api.py`**:

```python
# Line 426: Replace DocumentProcessor with EnhancedDocumentProcessor
from src.services.enhanced_document_processor import EnhancedDocumentProcessor

async def process_document_pipeline(document_id: int, file_path: str):
    # Use enhanced processor instead
    doc_processor = EnhancedDocumentProcessor()  # ← Change this line

    processing_result = await doc_processor.process_document(...)
```

## Lessons Learned

1. **Always trace the actual code path**
   - Don't assume - grep for the error message
   - Follow frontend API calls to find the real backend
   - Check which service is actually deployed

2. **Test with real failure cases**
   - Get the actual failing documents
   - Run them through the pipeline
   - Check logs at each step

3. **Verify integration before claiming "fixed"**
   - Run the actual frontend
   - Upload a test document
   - Verify the AI chat shows the correct response

4. **Understand the architecture first**
   - Map out all services and ports
   - Identify which service handles which endpoint
   - Check Docker Compose or deployment configs

5. **Add observability to black boxes**
   - Log OpenAI requests/responses
   - Log extracted text samples
   - Track success/failure metrics

## Recommended Immediate Actions

1. **Stop creating new code** until we:
   - Verify which service is actually running
   - Test with actual failing documents
   - Understand why extraction is failing

2. **Add debugging** to the ACTUAL pipeline:
   - Log extracted text length
   - Log OpenAI prompt/response
   - Log items found

3. **Test end-to-end**:
   - Upload → Process → Extract → Display
   - Verify each step succeeds
   - Fix actual failures, not theoretical ones

4. **Document the findings**:
   - What was the actual failure?
   - What was the root cause?
   - What was the fix?
   - How was it verified?

## Conclusion

The recurring failures are NOT because the code doesn't work.

The recurring failures are because:

1. **I was fixing the wrong code** (port 8000 instead of port 8002)
2. **I never tested with actual failures** (theoretical fixes only)
3. **I never verified deployment** (assumed code was running)
4. **I created parallel solutions** instead of fixing the real one

The REAL fix is:

✅ **Identify the actual failure** (debug logs + test documents)
✅ **Fix the actual code** (`src/nexus_backend_api.py` + `src/services/document_processor.py`)
✅ **Verify the fix works** (upload test → check database → check frontend)
✅ **Deploy correctly** (restart actual service on correct port)

Until we do this, no amount of new code will solve the problem.
