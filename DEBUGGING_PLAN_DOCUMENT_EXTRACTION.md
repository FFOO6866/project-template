# Debugging Plan: Document Extraction Failures

## Objective

**Find out WHY document extraction is failing** using systematic debugging, NOT creating more code.

## Phase 1: Verify Current State (5 minutes)

### 1.1 Check Running Services

```bash
# Windows
netstat -ano | findstr "8000 8001 8002"

# Expected output:
# TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       <PID>  ← core API
# TCP    0.0.0.0:8001           0.0.0.0:0              LISTENING       <PID>  ← websocket
# TCP    0.0.0.0:8002           0.0.0.0:0              LISTENING       <PID>  ← nexus backend ✅
```

**Validation**:
- [ ] Port 8002 is listening (nexus_backend_api.py)
- [ ] Can curl http://localhost:8002/api/health

### 1.2 Check Database State

```sql
-- Connect to database
psql -U horme_user -d horme_db

-- Check if documents table exists
\d documents

-- Check recent documents
SELECT id, name, ai_status,
       LENGTH(ai_extracted_data::text) as data_length,
       ai_confidence_score,
       upload_date
FROM documents
ORDER BY upload_date DESC
LIMIT 5;

-- Check a specific failed document
SELECT id, name, ai_status, ai_extracted_data
FROM documents
WHERE name LIKE '%Airways_Engineering%'
   OR name LIKE '%Waterfront_Resort%'
ORDER BY upload_date DESC
LIMIT 1;
```

**Validation**:
- [ ] Documents table exists
- [ ] Failed documents show `ai_status = 'completed'`
- [ ] `ai_extracted_data` has value (not NULL)
- [ ] Check if `ai_extracted_data->>'requirements'` exists
- [ ] Check if `ai_extracted_data->'requirements'->>'items'` is empty array

### 1.3 Check OpenAI Configuration

```bash
# Check environment variable
echo %OPENAI_API_KEY%  # Windows
echo $OPENAI_API_KEY   # Linux/Mac

# Test OpenAI API directly
python -c "
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
print(f'API Key configured: {bool(api_key)}')
print(f'API Key prefix: {api_key[:10] if api_key else None}...')

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4-turbo-preview',
        messages=[{'role': 'user', 'content': 'Say hello'}],
        max_tokens=10
    )
    print(f'OpenAI API Status: ✅ Working')
    print(f'Response: {response.choices[0].message.content}')
except Exception as e:
    print(f'OpenAI API Status: ❌ Failed')
    print(f'Error: {str(e)}')
"
```

**Validation**:
- [ ] OPENAI_API_KEY is set
- [ ] API key is valid (test succeeds)
- [ ] Model `gpt-4-turbo-preview` is accessible

## Phase 2: Add Debug Logging (10 minutes)

### 2.1 Modify DocumentProcessor to Log Everything

Edit `src/services/document_processor.py`:

```python
async def _extract_text(self, file_path: str) -> tuple[str, str]:
    """Extract text from document file"""
    file_ext = os.path.splitext(file_path)[1].lower()

    logger.info(f"🔍 [EXTRACT] File: {os.path.basename(file_path)}, Extension: {file_ext}")

    if file_ext == '.pdf':
        text, method = await self._extract_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        text = await self._extract_docx(file_path)
        method = 'docx'
    elif file_ext in ['.xlsx', '.xls']:
        text = await self._extract_excel(file_path)
        method = 'excel'
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

    # DEBUG LOGGING
    logger.info(f"📊 [EXTRACT] Method: {method}, Length: {len(text)} chars")
    logger.info(f"📝 [EXTRACT] First 300 chars:\n{text[:300]}")
    logger.info(f"📝 [EXTRACT] Last 300 chars:\n{text[-300:]}")

    # Look for table markers
    table_count = text.count("=== TABLE START ===")
    row_count = text.count("ROW:")
    logger.info(f"📋 [EXTRACT] Tables: {table_count}, Rows: {row_count}")

    return text, method

async def _analyze_requirements(self, text: str) -> Dict[str, Any]:
    """Analyze document text using OpenAI"""

    # DEBUG: Log text being sent to OpenAI
    text_to_send = text[:8000]
    logger.info(f"🤖 [OPENAI] Sending {len(text_to_send)} chars to OpenAI (original: {len(text)} chars)")

    if len(text) > 8000:
        logger.warning(f"⚠️ [OPENAI] Text truncated! Lost {len(text) - 8000} chars")

    prompt = f"""Analyze this Request for Quotation (RFP) document and extract ALL product line items.

Document text:
{text_to_send}

[...rest of prompt...]
"""

    logger.info(f"🤖 [OPENAI] Prompt length: {len(prompt)} chars")

    try:
        logger.info(f"🤖 [OPENAI] Calling API with model: {self.openai_model}")

        response = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing RFPs and extracting structured product requirements. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        requirements_json = response.choices[0].message.content

        # DEBUG: Log OpenAI response
        logger.info(f"✅ [OPENAI] Response received: {len(requirements_json)} chars")
        logger.info(f"📄 [OPENAI] Raw JSON response:\n{requirements_json[:1000]}")

        requirements = json.loads(requirements_json)

        # DEBUG: Log parsed requirements
        items_count = len(requirements.get('items', []))
        logger.info(f"📊 [OPENAI] Parsed requirements: {items_count} items found")

        if items_count > 0:
            logger.info(f"📦 [OPENAI] First 3 items:")
            for i, item in enumerate(requirements.get('items', [])[:3]):
                logger.info(f"   {i+1}. {item.get('description', 'N/A')} (qty: {item.get('quantity', 'N/A')})")
        else:
            logger.warning(f"⚠️ [OPENAI] NO ITEMS EXTRACTED!")
            logger.warning(f"⚠️ [OPENAI] Full response: {json.dumps(requirements, indent=2)}")

        return requirements

    except Exception as e:
        logger.error(f"❌ [OPENAI] API error: {str(e)}")
        logger.error(f"❌ [OPENAI] Exception type: {type(e).__name__}")
        raise RuntimeError(f"AI requirement extraction failed: {str(e)}")

async def process_document(
    self,
    document_id: int,
    file_path: str,
    db_pool: asyncpg.Pool
) -> Dict[str, Any]:
    """Main processing function with debug logging"""

    logger.info(f"🚀 [PROCESS] Starting document {document_id}: {file_path}")

    try:
        # Update status to processing
        await self._update_status(db_pool, document_id, "processing", None)
        logger.info(f"📝 [PROCESS] Status updated to 'processing'")

        # Extract text
        logger.info(f"📄 [PROCESS] Step 1: Extract text")
        text, extraction_method = await self._extract_text(file_path)

        # Analyze requirements
        logger.info(f"🤖 [PROCESS] Step 2: Analyze requirements")
        requirements = await self._analyze_requirements(text)

        # Package results
        extracted_data = {
            'requirements': requirements,
            'extraction_method': extraction_method,
            'processor_version': '1.1.0',
            'full_text_length': len(text)
        }

        # Update database
        logger.info(f"💾 [PROCESS] Step 3: Update database")
        await self._update_status(db_pool, document_id, "completed", extracted_data)

        logger.info(f"✅ [PROCESS] Document {document_id} processing complete")
        logger.info(f"📊 [PROCESS] Final stats: {len(requirements.get('items', []))} items extracted")

        return extracted_data

    except Exception as e:
        logger.error(f"❌ [PROCESS] Failed: {str(e)}")
        logger.error(f"❌ [PROCESS] Exception type: {type(e).__name__}")

        error_data = {'error': str(e)}
        await self._update_status(db_pool, document_id, "error", error_data)

        raise
```

### 2.2 Restart the Service

```bash
# Stop current service
pkill -f "nexus_backend_api" # Linux/Mac
# Or find and kill process on Windows: taskkill /F /PID <PID>

# Restart with console logging
python -m uvicorn src.nexus_backend_api:app --host 0.0.0.0 --port 8002 --reload --log-level info
```

## Phase 3: Test with Failing Document (15 minutes)

### 3.1 Get Test Document

If you don't have the actual failing documents:

```bash
# Create a test RFP DOCX with table
# Use Word to create a simple table:
# | Item | Quantity | Unit |
# |------|----------|------|
# | DEWALT DCD791D2 20V Cordless Drill | 50 | units |
# | 3M H-700 Safety Helmet | 100 | units |

# Save as: test_rfq.docx
```

### 3.2 Upload Document

```bash
curl -X POST http://localhost:8002/api/files/upload \
  -F "file=@test_rfq.docx" \
  -F "document_type=rfp" \
  -F "category=procurement"

# Response will include document_id
# {"message": "File uploaded successfully...", "document_id": 123, ...}
```

### 3.3 Watch Logs

In the console where uvicorn is running, you should see:

```
🚀 [PROCESS] Starting document 123: /app/uploads/abc123_test_rfq.docx
📝 [PROCESS] Status updated to 'processing'
📄 [PROCESS] Step 1: Extract text
🔍 [EXTRACT] File: abc123_test_rfq.docx, Extension: .docx
📊 [EXTRACT] Method: docx, Length: 456 chars
📝 [EXTRACT] First 300 chars:
Request for Quotation
...
=== TABLE START ===
HEADERS: Item | Quantity | Unit
ROW: DEWALT DCD791D2 20V Cordless Drill | 50 | units
...
📋 [EXTRACT] Tables: 1, Rows: 2
🤖 [PROCESS] Step 2: Analyze requirements
🤖 [OPENAI] Sending 456 chars to OpenAI (original: 456 chars)
🤖 [OPENAI] Calling API with model: gpt-4-turbo-preview
✅ [OPENAI] Response received: 567 chars
📊 [OPENAI] Parsed requirements: 2 items found
📦 [OPENAI] First 3 items:
   1. DEWALT DCD791D2 20V Cordless Drill (qty: 50)
   2. 3M H-700 Safety Helmet (qty: 100)
💾 [PROCESS] Step 3: Update database
✅ [PROCESS] Document 123 processing complete
📊 [PROCESS] Final stats: 2 items extracted
```

### 3.4 Check Database

```sql
SELECT id, name, ai_status,
       ai_extracted_data->'requirements'->'items' as items
FROM documents
WHERE id = 123;
```

### 3.5 Check Frontend

```bash
# Poll the endpoint frontend uses
curl http://localhost:8002/api/documents/123 | jq .

# Should see:
{
  "id": 123,
  "name": "test_rfq.docx",
  "ai_status": "completed",
  "ai_extracted_data": {
    "requirements": {
      "items": [
        {
          "description": "DEWALT DCD791D2 20V Cordless Drill",
          "quantity": 50,
          ...
        },
        ...
      ]
    }
  }
}
```

## Phase 4: Diagnose Actual Failure (10 minutes)

### Scenario A: Extraction Returns Empty Text

**Symptoms**:
```
📊 [EXTRACT] Method: docx, Length: 0 chars
```

**Diagnosis**: File extraction failed

**Fix**: Check if python-docx is installed:
```bash
pip install python-docx
```

### Scenario B: Text Extracted But Truncated

**Symptoms**:
```
⚠️ [OPENAI] Text truncated! Lost 15000 chars
📊 [OPENAI] Parsed requirements: 0 items found
```

**Diagnosis**: Document is too long, items are after 8000 chars

**Fix**: Modify `src/services/document_processor.py` line 423:
```python
# OLD: text[:8000]
# NEW: Smarter truncation
text_to_send = self._smart_truncate(text, 8000)

def _smart_truncate(self, text: str, max_chars: int) -> str:
    """Truncate text but prioritize tables"""
    if len(text) <= max_chars:
        return text

    # Find all table sections
    tables = []
    pos = 0
    while True:
        start = text.find("=== TABLE START ===", pos)
        if start == -1:
            break
        end = text.find("=== TABLE END ===", start)
        if end == -1:
            break
        tables.append((start, end + len("=== TABLE END ===")))
        pos = end

    if not tables:
        # No tables, just truncate from start
        return text[:max_chars]

    # Calculate total table size
    total_table_size = sum(end - start for start, end in tables)

    if total_table_size <= max_chars:
        # All tables fit, extract them
        result = ""
        for start, end in tables:
            result += text[start:end] + "\n\n"
        return result[:max_chars]
    else:
        # Tables too big, take as many as fit
        result = ""
        for start, end in tables:
            table_text = text[start:end]
            if len(result) + len(table_text) > max_chars:
                break
            result += table_text + "\n\n"
        return result
```

### Scenario C: OpenAI Returns Empty Items

**Symptoms**:
```
✅ [OPENAI] Response received: 234 chars
📊 [OPENAI] Parsed requirements: 0 items found
⚠️ [OPENAI] Full response: {"items": [], "customer_name": "..."}
```

**Diagnosis**: OpenAI couldn't extract items from the text format

**Fix**: Check the `📄 [OPENAI] Raw JSON response` and see what OpenAI said:
- If items are in the response but structured differently → adjust parsing
- If OpenAI says "no products found" → improve prompt or use EnhancedProcessor

### Scenario D: OpenAI API Fails

**Symptoms**:
```
❌ [OPENAI] API error: Invalid API key
```

**Diagnosis**: Configuration issue

**Fix**: Set correct API key in environment

## Phase 5: Implement Actual Fix (Varies)

Based on the diagnosis, implement ONE of these fixes:

### Fix A: Integrate EnhancedDocumentProcessor

If basic DocumentProcessor is insufficient:

```python
# In src/nexus_backend_api.py, line 426
from src.services.enhanced_document_processor import EnhancedDocumentProcessor

async def process_document_pipeline(document_id: int, file_path: str):
    # Use enhanced processor
    doc_processor = EnhancedDocumentProcessor()  # ← Change here

    processing_result = await doc_processor.process_document(
        document_id,
        file_path,
        api_instance.db_pool
    )
    # Rest stays the same
```

### Fix B: Improve Truncation Logic

If text is getting truncated:

```python
# Implement smart truncation as shown in Scenario B
```

### Fix C: Handle Specific Document Formats

If certain formats fail:

```python
# Add format-specific handlers in DocumentProcessor
```

## Phase 6: Verify Fix (10 minutes)

1. **Restart service** with changes
2. **Upload test document** again
3. **Check logs** - should see items extracted
4. **Check database** - should have items in JSON
5. **Check frontend** - should show items in chat

## Success Criteria

✅ Debug logs show:
- Text extraction succeeds
- OpenAI returns items
- Database updated with items
- Frontend displays items

✅ Frontend chat shows:
```
"Done. Found 2 items in 'test_rfq.docx'..."
```

NOT:
```
"Couldn't pull anything specific from 'test_rfq.docx'..."
```

## Documentation

After successful fix, document:

1. **What was the actual problem?**
2. **What was the root cause?**
3. **What was the fix?**
4. **How was it verified?**
5. **How to prevent in future?**

This information goes in a new file: `DOCUMENT_EXTRACTION_FIX_VERIFIED.md`
