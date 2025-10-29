# Manual Frontend Restoration Guide
**Date**: 2025-10-21
**Purpose**: Restore frontend to 100% original state by reverting my modifications

---

## Files That Need Manual Restoration

### File 1: `frontend/validate-env.js`

**Lines to Change**: 84-86

**Current (Modified by me)**:
```javascript
        if (!value.startsWith('http://') && !value.startsWith('https://') &&
            !value.startsWith('ws://') && !value.startsWith('wss://')) {
          return { valid: false, message: 'MCP URL must start with http://, https://, ws://, or wss://' };
```

**Original Version**:
```javascript
        if (!value.startsWith('http://') && !value.startsWith('https://')) {
          return { valid: false, message: 'MCP URL must start with http:// or https://' };
```

**How to restore**:
1. Open `frontend/validate-env.js`
2. Go to line 84
3. Remove `&& !value.startsWith('ws://') && !value.startsWith('wss://')` from line 84-85
4. Change line 86 message to: `'MCP URL must start with http:// or https://'`

---

### File 2: `frontend/lib/api-types.ts`

**Lines to Remove**: 57-78

**Current (Modified by me)**:
```typescript
export interface Document {
  id: number;
  filename: string;
  content_type: string;
  size: number;
  document_type?: string;
  uploaded_at: string;
  uploaded_by?: number;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  metadata?: DocumentMetadata;
  // Additional fields from backend API JOIN queries  ← REMOVE THIS LINE
  customer_name?: string;      // ← REMOVE THIS LINE
  customer_id?: number;        // ← REMOVE THIS LINE
  file_path?: string;          // ← REMOVE THIS LINE
  file_size?: number;          // ← REMOVE THIS LINE
  mime_type?: string;          // ← REMOVE THIS LINE
  upload_date?: string;        // ← REMOVE THIS LINE
  ai_status?: string;          // ← REMOVE THIS LINE
  ai_extracted_data?: any;     // ← REMOVE THIS LINE
  ai_confidence_score?: number;// ← REMOVE THIS LINE
  contact_person?: string;     // ← REMOVE THIS LINE
  processing_status?: string;  // ← REMOVE THIS LINE
  ai_summary?: string;         // ← REMOVE THIS LINE
  key_points?: string[];       // ← REMOVE THIS LINE
  customer_details?: any;      // ← REMOVE THIS LINE
  rfp_details?: any;           // ← REMOVE THIS LINE
  requirements?: any;          // ← REMOVE THIS LINE
  ai_analysis?: any;           // ← REMOVE THIS LINE
  generated_quote?: any;       // ← REMOVE THIS LINE
  name?: string;               // ← REMOVE THIS LINE
  type?: string;               // ← REMOVE THIS LINE
  category?: string;           // ← REMOVE THIS LINE
}
```

**Original Version** (best guess):
```typescript
export interface Document {
  id: number;
  filename: string;
  content_type: string;
  size: number;
  document_type?: string;
  uploaded_at: string;
  uploaded_by?: number;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  metadata?: DocumentMetadata;
}
```

**How to restore**:
1. Open `frontend/lib/api-types.ts`
2. Go to line 57 (the comment "// Additional fields from backend API JOIN queries")
3. Delete lines 57-78 (all the fields I added)
4. The interface should end with just `metadata?: DocumentMetadata;` before the closing brace

---

### File 3: `frontend/lib/api-client-usage.example.ts`

**Status**: Deleted by me

**Action**: If this file existed in your original frontend, restore it from your backup

---

## Step-by-Step Restoration Process

### Step 1: Locate Your Original Backup

You mentioned you "reloaded the backup" and some files (tsconfig.json, icons.tsx) successfully reverted. Where did those files come from?

Possible locations:
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov-backup`
- `C:\Users\fujif\Desktop\frontend-backup`
- A .zip file you downloaded
- Another git branch or repository

### Step 2: Copy Original Files

Once you find the backup location, copy these files:

```bash
# From your backup location, copy:
validate-env.js → C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\frontend\validate-env.js
lib\api-types.ts → C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\frontend\lib\api-types.ts
lib\api-client-usage.example.ts → C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\frontend\lib\api-client-usage.example.ts
```

### Step 3: OR Manually Edit Files

If you can't find the backup, use the editing instructions above to manually revert the changes.

---

## Verification After Restoration

After restoring, verify 100% original state:

### Check 1: validate-env.js
```bash
grep -n "ws://" frontend/validate-env.js
```
**Expected**: No matches (WebSocket protocols removed)

### Check 2: api-types.ts
```bash
grep -n "customer_name\|contact_person\|processing_status" frontend/lib/api-types.ts
```
**Expected**: No matches (extra fields removed)

### Check 3: File count
```bash
ls frontend/lib/api-*.ts
```
**Expected**: Both `api-types.ts` and `api-client-usage.example.ts` should exist

---

## After Restoration: Backend Compatibility Issues

**WARNING**: After restoring to 100% original frontend, you will have field name mismatches with the backend:

| Frontend Expects | Backend Provides | Result |
|------------------|------------------|--------|
| `filename` | `name` | ❌ `undefined` |
| `content_type` | `type` | ❌ `undefined` |
| `size` | `file_size` | ❌ `undefined` |
| `uploaded_at` | `upload_date` | ❌ `undefined` |

**To fix these issues, you will need to either**:

1. **Modify backend** to use field aliases:
   ```sql
   SELECT
     d.name AS filename,
     d.type AS content_type,
     d.file_size AS size,
     d.upload_date AS uploaded_at
   FROM documents d
   ```

2. **Add frontend adapter layer** to map backend responses:
   ```typescript
   const mapBackendDocument = (doc: any): Document => ({
     ...doc,
     filename: doc.name,
     content_type: doc.type,
     size: doc.file_size,
     uploaded_at: doc.upload_date,
   });
   ```

---

## Alternative: Tell Me Your Backup Location

If you can tell me where your original files are located (the place where you got tsconfig.json and icons.tsx), I can copy the remaining files automatically.

Example:
```
C:\Users\fujif\Desktop\horme-frontend-backup
C:\Users\fujif\Downloads\frontend-original
Z:\Backups\horme-pov\frontend
```

Just provide the full path and I'll complete the restoration.

---

## Summary

**To restore to 100% original**:

1. Find where you got the tsconfig.json and icons.tsx that successfully reverted
2. Copy `validate-env.js` and `lib/api-types.ts` from that same backup location
3. OR manually edit using the instructions above
4. After restoration, expect frontend-backend compatibility issues that need resolution

**Current Status**:
- ✅ 3 files restored (tsconfig.json, icons.tsx, .env.test)
- ❌ 2 files still modified (validate-env.js, api-types.ts)
- ❌ 1 file missing (api-client-usage.example.ts)
