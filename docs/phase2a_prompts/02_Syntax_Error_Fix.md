# 🐛 PROMPT #2: Video Assembler Syntax Error Fix

## Phase 2A - Critical Issue Resolution

**Reference Code:** `[REF:PROMPT-002]`  
**Complexity:** ⚡ Low  
**Estimated Time:** 5-10 minutes  
**Prerequisites:** PROMPT #1 complete

---

## 🎯 OBJECTIVE

Fix the syntax error in `src/services/video_assembler.py` at line 558 where `await` is used outside of an async function, blocking video generation.

**Error:**

```
SyntaxError: 'await' outside async function (video_assembler.py, line 558)
```

---

## 📋 COPILOT PROMPT

````
GITHUB COPILOT DIRECTIVE: FIX VIDEO ASSEMBLER SYNTAX ERROR
[REF:PROMPT-002]

CONTEXT:
- Project: Faceless YouTube Automation Platform v2.0
- Phase: 2A - Critical Issue Resolution
- File: src/services/video_assembler.py
- Error Location: Line 558
- Error Type: SyntaxError - 'await' outside async function

CURRENT STATE:
Diagnostic script reports:
❌ FAILED: Import src.services.video_assembler
   Error: 'await' outside async function (video_assembler.py, line 558)

Impact: Video generation service cannot be imported, blocks all video creation

TASK:
1. Open src/services/video_assembler.py
2. Navigate to line 558
3. Analyze the context around the await statement
4. Determine the correct fix (add async to function OR remove await)
5. Apply the fix
6. Test the import
7. Verify video_assembler can be used

SPECIFIC ACTIONS:

Step 1: Open the File
Open src/services/video_assembler.py in VS Code editor

Step 2: Locate the Error
Go to line 558 (Ctrl+G in VS Code)
Look for code like:
```python
await some_function()
````

Step 3: Analyze Context
Examine the function containing line 558:

- Is it defined as `def function_name()` or `async def function_name()`?
- Does the function need to be async?
- Is there a reason this needs to await?

Step 4: Determine Fix Strategy
Choose one of these fixes:

OPTION A: Make Function Async (if it calls async operations)

```python
# Before
def process_video():
    ...
    await some_async_function()  # Line 558

# After
async def process_video():
    ...
    await some_async_function()  # Now valid
```

OPTION B: Remove await (if function is actually synchronous)

```python
# Before
def process_video():
    ...
    await some_async_function()  # Line 558

# After
def process_video():
    ...
    some_async_function()  # Remove await
```

OPTION C: Use asyncio.run() (if isolated async call)

```python
# Before
def process_video():
    ...
    await some_async_function()  # Line 558

# After
import asyncio

def process_video():
    ...
    asyncio.run(some_async_function())  # Run async in sync context
```

Step 5: Apply the Fix
Implement the chosen solution based on the code analysis

Step 6: Test Import
Execute in terminal:

```powershell
python -c "from src.services.video_assembler import VideoAssembler; print('✅ Import successful')"
```

Step 7: Run Diagnostic
Execute in terminal:

```powershell
python scripts/diagnostics.py
```

Check that video_assembler test now passes

REQUIREMENTS:

- VS Code open with src/services/video_assembler.py
- Understanding of async/await in Python
- Ability to analyze code context

ERROR HANDLING:

- If unsure which fix to apply, use OPTION A (make function async)
- If new errors appear, check caller functions also need to be async
- If import still fails, check for other syntax errors in file

DELIVERABLES:

1. Fixed src/services/video_assembler.py (syntax error resolved)
2. Successful import test
3. Updated diagnostic showing video_assembler passes
4. Git commit with the fix

SUCCESS CRITERIA:
✅ No syntax error at line 558
✅ `from src.services.video_assembler import VideoAssembler` works
✅ Diagnostic test for video_assembler passes
✅ File saved and committed

NEXT STEP:
Once complete, proceed to PROMPT #3 (Database Setup)

````

---

## 🔍 DETAILED INSTRUCTIONS

### Step 1: Open File in VS Code

```powershell
# From terminal
code src/services/video_assembler.py
````

Or use VS Code:

- Press `Ctrl+P`
- Type: `video_assembler.py`
- Press Enter

### Step 2: Navigate to Line 558

- Press `Ctrl+G`
- Type: `558`
- Press Enter

### Step 3: Read the Context

Examine the function containing the error:

```python
# Example of what you might see:
def assemble_video_clips(self, clips, output_path):
    """Assemble video clips into final video."""
    # ... some code ...

    await self.process_async_operation()  # ← Line 558 ERROR

    # ... more code ...
```

**Key Questions:**

1. Is this function defined with `def` or `async def`?
2. Are there other `await` statements in this function?
3. Does the function signature need to change?
4. Who calls this function? (Check other files)

### Step 4: Implement Fix

#### Most Likely Scenario: Make Function Async

If the function legitimately needs to await async operations:

```python
# BEFORE
def assemble_video_clips(self, clips, output_path):
    await self.process_async_operation()  # ERROR

# AFTER
async def assemble_video_clips(self, clips, output_path):
    await self.process_async_operation()  # ✅ Valid
```

**Important:** If you make this function async, check where it's called from!

### Step 5: Check Callers

Search for uses of the fixed function:

- Press `Ctrl+Shift+F` (Find in Files)
- Search for: `assemble_video_clips(`
- Check each caller

If caller is also not async, it needs to either:

1. Become async and use `await`, or
2. Use `asyncio.run()` to call the async function

### Step 6: Test the Fix

```powershell
# Test import
python -c "from src.services.video_assembler import VideoAssembler; print('✅ Import successful')"
```

**Expected:** `✅ Import successful`

### Step 7: Verify with Diagnostics

```powershell
python scripts/diagnostics.py
```

Look for:

```
Component: Application Services
  ✅ PASSED: Import src.services.video_assembler
```

---

## ⚠️ TROUBLESHOOTING

### Issue: Made function async, but now callers fail

**Solution:**
Update callers to use `await`:

```python
# Caller needs update
async def caller_function():
    result = await assemble_video_clips(clips, path)  # Add await
```

### Issue: Multiple await errors

**Solution:**
The entire function likely needs to be async. Make sure:

1. Function is `async def`
2. All await statements are inside async functions
3. Callers properly await the function

### Issue: Import still fails

**Check for:**

```powershell
# Look for other syntax errors
python -m py_compile src/services/video_assembler.py
```

### Issue: Not sure if function should be async

**Rule of Thumb:**

- If function calls any `await` → Make it `async def`
- If function does I/O (network, disk) → Consider making it async
- If function is pure computation → Keep it `def`

---

## ✅ SUCCESS VERIFICATION

### Checklist

- [ ] Line 558 syntax error is fixed
- [ ] Import test passes without errors
- [ ] Diagnostic test for video_assembler passes
- [ ] No new errors introduced
- [ ] File saved

### Verification Commands

```powershell
# Test 1: Import
python -c "from src.services.video_assembler import VideoAssembler; print('✅ Import OK')"

# Test 2: Instantiate
python -c "from src.services.video_assembler import VideoAssembler; va = VideoAssembler(); print('✅ Instantiation OK')"

# Test 3: Run diagnostics
python scripts/diagnostics.py | Select-String "video_assembler"
```

**Expected Output:**

```
✅ Import OK
✅ Instantiation OK
✅ PASSED: Import src.services.video_assembler
```

---

## 📊 BEFORE & AFTER

### Before

```
Component: Application Services - UNHEALTHY ❌
  ❌ FAILED: Import src.services.video_assembler
     Error: 'await' outside async function (line 558)

Status: Video generation BLOCKED
```

### After

```
Component: Application Services - IMPROVED ✅
  ✅ PASSED: Import src.services.video_assembler

Status: Video generation READY (after dependencies installed)
```

---

## 🎯 NEXT STEPS

Once the syntax error is fixed:

1. **Commit the fix:**

   ```powershell
   git add src/services/video_assembler.py
   git commit -m "fix(video-assembler): resolve await syntax error at line 558"
   ```

2. **Proceed to PROMPT #3:** [Database Setup](03_Database_Setup.md)

3. **Mark this task complete** in your checklist

**Status Update:**

- ✅ Critical Issue #1: RESOLVED
- ✅ Critical Issue #2: RESOLVED
- ⏳ Critical Issue #3: Next
- ⏳ Critical Issue #4: Pending
- ⏳ Critical Issue #5: Pending
- ⏳ Critical Issue #6: Pending

---

## 🧠 LEARNING NOTE

**Async/Await in Python:**

- `async def` declares an async function
- `await` can ONLY be used inside `async def` functions
- To call async function from sync code: `asyncio.run(async_function())`
- Async is contagious: if function A awaits, callers of A must also await

**Common Pattern:**

```python
# Async function
async def fetch_data():
    await asyncio.sleep(1)
    return "data"

# Sync caller
def sync_function():
    result = asyncio.run(fetch_data())  # OK

# Async caller
async def async_function():
    result = await fetch_data()  # OK
```

---

_Reference: ISSUES_FOUND.md (Issue #3), diagnostic_report.txt_  
_Generated: October 4, 2025_
