# Standardized UAT Resolution Process

## Quick Start Prompt Template
```
I need to fix UAT issue REFMGT-XXX: [Issue description]
Please follow the standardized UAT process to analyze, implement, test, and deploy the fix.
```

## Phase 1: Analysis & Understanding

### 1.1 Initial Issue Assessment
**Prompt**: `Analyze REFMGT-XXX issue: [describe the problem]. What are the symptoms and expected behavior?`

### 1.2 Deep Analysis (if needed)
**Prompt**: `ultrathink-analyst: Analyze the root cause of [issue description] in the HMI chatbot system`

### 1.3 Codebase Research
**Prompt**: `Search for relevant code patterns related to [feature/issue] in the hmi-chatbot codebase`

**Key Files to Check**:
- `main.py` - Core request handling and workflow orchestration
- `workflows/` - Workflow definitions
- `nodes/` - Individual node implementations
- `tests/uat/` - Previous UAT fixes and patterns

## Phase 2: Implementation Planning

### 2.1 Create Task List
**Prompt**: `Create a TodoWrite task list for fixing REFMGT-XXX`

**Standard Tasks**:
1. Analyze issue and identify root cause
2. Create/checkout feature branch
3. Implement fix in local repository
4. Test fix locally
5. Commit and push changes
6. Deploy to VM for testing
7. Validate fix on VM
8. Document resolution

### 2.2 Branch Management
```bash
# Always work on a feature branch
git -C "C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot" checkout -b refmgt-xxx-fix
```

## Phase 3: Implementation

### 3.1 Code Modification Strategy
**CRITICAL**: Always modify the LOCAL repository first, not the VM directly!

**Local Repository Path**: `C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot`

### 3.2 Common Fix Patterns

#### Pattern A: Greeting/Response Issues
```python
# Check if message is a greeting for new sessions
user_message_lower = user_message.lower().strip()
is_greeting = user_message_lower in ["hello", "hi", "hey"]
is_new_session = len(current_state_dict.get("conversation_history", [])) <= 1

if is_greeting and is_new_session:
    # Handle greeting logic
    # Skip workflow processing
else:
    # Normal workflow processing
    updated_state_dict = await graph.ainvoke(current_state_dict)
```

#### Pattern B: State Management Issues
```python
# Ensure state contains required fields
if "field_name" not in current_state_dict:
    current_state_dict["field_name"] = default_value
```

### 3.3 Testing Locally
**Prompt**: `Test the REFMGT-XXX fix locally before deployment`

## Phase 4: Version Control

### 4.1 Commit Changes
```bash
git -C "C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot" add .
git -C "C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot" commit -m "fix(REFMGT-XXX): [Brief description]

- [Detailed change 1]
- [Detailed change 2]
- [Test results]"
```

### 4.2 Push to GitHub
```bash
git -C "C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot" push origin refmgt-xxx-fix
```

## Phase 5: VM Deployment & Testing

### 5.1 VM Connection Details
- **Host**: 18.136.214.139
- **User**: ubuntu
- **Key**: `C:\Users\fujif\OneDrive\Desktop\hmi.pem`
- **Directory**: `/opt/hmi-chatbot`

### 5.2 Deployment Options

#### Option A: Git Pull (Preferred if GitHub auth works)
```bash
ssh -i "C:\Users\fujif\OneDrive\Desktop\hmi.pem" ubuntu@18.136.214.139 "cd /opt/hmi-chatbot && git pull origin refmgt-xxx-fix"
```

#### Option B: Direct File Copy (If GitHub auth fails)
```bash
# Create patch from local changes
git -C "C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot" diff > fix.patch

# Copy and apply patch
scp -i "C:\Users\fujif\OneDrive\Desktop\hmi.pem" fix.patch ubuntu@18.136.214.139:/tmp/
ssh -i "C:\Users\fujif\OneDrive\Desktop\hmi.pem" ubuntu@18.136.214.139 "cd /opt/hmi-chatbot && sudo patch -p1 < /tmp/fix.patch"
```

### 5.3 Restart Services
```bash
ssh -i "C:\Users\fujif\OneDrive\Desktop\hmi.pem" ubuntu@18.136.214.139 "cd /opt/hmi-chatbot && sudo docker compose restart app"
```

### 5.4 Test on VM
```bash
# Wait for service to start
sleep 30

# Test the fix
ssh -i "C:\Users\fujif\OneDrive\Desktop\hmi.pem" ubuntu@18.136.214.139 "curl -X POST http://localhost:8000/whatsapp/message -H 'Content-Type: application/json' -d '{\"session_id\": \"test_xxx\", \"user_message\": \"[test message]\", \"patient_details\": {\"patient_name\": \"Test Patient\", \"patient_id\": \"TEST123\"}}'"
```

## Phase 6: Documentation

### 6.1 Create UAT Folder
```bash
mkdir -p "C:\Users\fujif\OneDrive\Documents\GitHub\hmi-chatbot\tests\uat\REFMGT-XXX"
```

### 6.2 Resolution Report Template
Create `FINAL_RESOLUTION.md`:
```markdown
# REFMGT-XXX Final Resolution

## Issue Description
[What was the problem?]

## Root Cause
[Why did it happen?]

## Solution Implemented
[What changes were made?]

### Code Changes
```python
# Show the key code changes
```

## Testing Results
- Before: [Previous behavior]
- After: [Fixed behavior]

## Deployment Notes
- Branch: refmgt-xxx-fix
- Tested on VM: 18.136.214.139
- Status: ✅ Resolved
```

## Common Pitfalls to Avoid

### ❌ DON'T:
1. Edit files directly on the VM without updating local repository
2. Use `request` object in `process_chat_message` function
3. Forget to test after Docker restart
4. Apply multiple patches without tracking changes
5. Skip the TodoWrite task tracking

### ✅ DO:
1. Always work in local repository first
2. Use `current_state_dict` for accessing state variables
3. Wait 20-30 seconds after Docker restart before testing
4. Create backups before applying patches
5. Document every change in git commits

## Validation Checklist

- [ ] Issue reproduced and understood
- [ ] Fix implemented in local repository
- [ ] Changes committed to feature branch
- [ ] Pushed to GitHub
- [ ] Deployed to VM (via git pull or patch)
- [ ] Docker services restarted
- [ ] Fix tested on VM with multiple scenarios
- [ ] Documentation created
- [ ] All TodoWrite tasks marked as completed

## Emergency Rollback

If something goes wrong on the VM:
```bash
# Restore from backup
ssh -i "C:\Users\fujif\OneDrive\Desktop\hmi.pem" ubuntu@18.136.214.139 "cd /opt/hmi-chatbot && sudo cp main.py.backup main.py && sudo docker compose restart app"
```

## Success Metrics

A UAT fix is considered successful when:
1. The reported issue is resolved
2. No regression in existing functionality
3. Fix is in version control (GitHub)
4. VM testing shows consistent positive results
5. Documentation is complete

---

**Remember**: The VM is just a test environment. Always ensure changes are properly committed to the GitHub repository!