# 🔧 PROMPT #1: Python Dependencies Installation

## Phase 2A - Critical Issue Resolution

**Reference Code:** `[REF:PROMPT-001]`  
**Complexity:** ⚡ Low  
**Estimated Time:** 10-30 minutes  
**Prerequisites:** None

---

## 🎯 OBJECTIVE

Install all 28 missing Python packages required for core functionality including video generation, YouTube uploads, and AI processing.

**Critical Packages to Install:**

- `moviepy` - Video assembly engine
- `google-api-python-client` - YouTube API client
- `google-auth-oauthlib` - OAuth authentication
- `sentence-transformers` - AI embeddings
- Plus 24 additional dependencies

---

## 📋 COPILOT PROMPT

````
GITHUB COPILOT DIRECTIVE: PYTHON DEPENDENCIES INSTALLATION
[REF:PROMPT-001]

CONTEXT:
- Project: Faceless YouTube Automation Platform v2.0
- Phase: 2A - Critical Issue Resolution
- Task: Install 28 missing Python packages
- Location: C:\FacelessYouTube
- Virtual Environment: venv\ (should be active)
- Requirements File: requirements.txt

CURRENT STATE:
Phase 1 diagnostic identified 28 critical missing packages:
- moviepy - CRITICAL (video generation blocked)
- google-api-python-client - CRITICAL (YouTube uploads blocked)
- google-auth-oauthlib - CRITICAL (OAuth blocked)
- sentence-transformers - HIGH (AI embeddings)
- Plus: numpy, scipy, torch, pillow, ffmpeg-python, and 19 others

Impact: Backend cannot start, video generation fails, uploads blocked

TASK:
1. Verify virtual environment is active
2. Check Python version (must be 3.8+)
3. Install all packages from requirements.txt
4. Verify installation success
5. Test critical imports
6. Update diagnostic report

SPECIFIC ACTIONS:

Step 1: Verify Environment
Execute in terminal:
```powershell
# Check venv is active (should see (venv) in prompt)
python --version
# Should show Python 3.8 or higher
````

Step 2: Install All Dependencies
Execute in terminal:

```powershell
pip install -r requirements.txt
```

Expected behavior:

- Installation should take 5-15 minutes
- Some packages may have large downloads (torch ~2GB, tensorflow ~500MB)
- Watch for errors or failures

Step 3: Verify Critical Packages
Execute in terminal:

```powershell
python -c "import moviepy.editor; print('✅ moviepy installed')"
python -c "import googleapiclient; print('✅ google-api-python-client installed')"
python -c "import google_auth_oauthlib; print('✅ google-auth-oauthlib installed')"
python -c "import sentence_transformers; print('✅ sentence-transformers installed')"
python -c "import torch; print('✅ torch installed')"
python -c "import PIL; print('✅ pillow installed')"
```

All should print ✅ without errors

Step 4: Run Dependency Audit
Execute in terminal:

```powershell
python scripts/audit_dependencies.py > dependency_audit_post_install.txt
```

Review output - should show 0 missing packages (down from 28)

Step 5: Test Import in Script
Create a simple test to verify all critical imports work together.

REQUIREMENTS:

- Virtual environment must be active
- requirements.txt must exist in project root
- Internet connection required for package downloads
- Sufficient disk space (~5GB for all packages)

ERROR HANDLING:
If installation fails:

1. Check internet connection
2. Verify pip is up to date: `pip install --upgrade pip`
3. Try installing problematic package individually
4. Check for Windows-specific build requirements
5. Consult error messages for missing C++ build tools

DELIVERABLES:

1. All packages installed successfully
2. Import verification passes for all critical packages
3. Updated dependency audit showing 0 missing
4. Terminal output saved as evidence

SUCCESS CRITERIA:
✅ pip install completes without errors
✅ All 6 critical imports work
✅ Dependency audit shows 0 missing packages
✅ No import errors when importing main modules

NEXT STEP:
Once complete, proceed to PROMPT #2 (Syntax Error Fix)

````

---

## 🔍 DETAILED INSTRUCTIONS

### Step 1: Activate Virtual Environment

```powershell
# If not already active
cd C:\FacelessYouTube
.\venv\Scripts\Activate.ps1
````

You should see `(venv)` in your terminal prompt.

### Step 2: Upgrade pip (Recommended)

```powershell
python -m pip install --upgrade pip
```

This ensures you have the latest package installer.

### Step 3: Install All Dependencies

```powershell
pip install -r requirements.txt
```

**Expected Output:**

```
Collecting moviepy==X.X.X
Downloading moviepy-X.X.X-py3-none-any.whl
...
Successfully installed moviepy-X.X.X google-api-python-client-X.X.X ...
```

**Installation Time:**

- Fast internet: 5-10 minutes
- Slow internet: 15-30 minutes
- Large packages: torch (~2GB), tensorflow (~500MB if listed)

### Step 4: Verify Critical Imports

Copy and paste each command to verify:

```powershell
python -c "import moviepy.editor; print('✅ moviepy installed')"
python -c "import googleapiclient; print('✅ google-api-python-client installed')"
python -c "import google_auth_oauthlib; print('✅ google-auth-oauthlib installed')"
python -c "import sentence_transformers; print('✅ sentence-transformers installed')"
python -c "import torch; print('✅ torch installed')"
python -c "import PIL; print('✅ pillow installed')"
```

### Step 5: Run Updated Audit

```powershell
python scripts/audit_dependencies.py
```

**Expected Output:**

```
Missing packages: 0 (was 28)
Version mismatches: 41 (acceptable)
Potentially unused: 324 (can ignore)
```

---

## ⚠️ TROUBLESHOOTING

### Issue: "pip: command not found"

**Solution:**

```powershell
python -m pip install -r requirements.txt
```

### Issue: "Could not find a version that satisfies the requirement..."

**Solution:**
Check requirements.txt for outdated version pins. Try:

```powershell
pip install moviepy  # Without version constraint
```

### Issue: "Microsoft Visual C++ 14.0 is required"

**Solution (Windows):**
Some packages need C++ build tools:

1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Retry installation

### Issue: Torch installation slow/fails

**Solution:**
Install CPU-only version (much smaller):

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Out of disk space

**Check Space:**

```powershell
Get-PSDrive C | Select-Object Used,Free
```

**Solution:**
Free up at least 5GB before installing.

---

## ✅ SUCCESS VERIFICATION

### Checklist

- [ ] Virtual environment is active
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] All 6 critical import tests passed
- [ ] Dependency audit shows 0 missing packages
- [ ] No error messages in terminal

### Verification Command

Run this comprehensive test:

```powershell
python -c "
import sys
try:
    import moviepy.editor
    import googleapiclient
    import google_auth_oauthlib
    import sentence_transformers
    import torch
    import PIL
    print('✅ ALL CRITICAL PACKAGES INSTALLED SUCCESSFULLY')
    sys.exit(0)
except ImportError as e:
    print(f'❌ IMPORT FAILED: {e}')
    sys.exit(1)
"
```

**Expected:** `✅ ALL CRITICAL PACKAGES INSTALLED SUCCESSFULLY`

---

## 📊 BEFORE & AFTER

### Before

```
Missing packages: 28
Status: Backend cannot start
Video generation: BLOCKED
YouTube uploads: BLOCKED
AI processing: BLOCKED
```

### After

```
Missing packages: 0
Status: All dependencies available
Video generation: READY
YouTube uploads: READY (after OAuth setup)
AI processing: READY
```

---

## 🎯 NEXT STEPS

Once all packages are installed successfully:

1. **Save terminal output** for your records
2. **Proceed to PROMPT #2:** [Video Assembler Syntax Fix](02_Syntax_Error_Fix.md)
3. **Mark this task complete** in your checklist

**Status Update:**

- ✅ Critical Issue #1: RESOLVED
- ⏳ Critical Issue #2: Next
- ⏳ Critical Issue #3: Pending
- ⏳ Critical Issue #4: Pending
- ⏳ Critical Issue #5: Pending
- ⏳ Critical Issue #6: Pending

---

## 📝 NOTES

- **Installation is one-time:** Once installed, packages persist in venv
- **Version mismatches are OK:** 41 mismatches identified are mostly compatible
- **Unused packages:** 324 unused packages can be cleaned up later (low priority)
- **Internet required:** All packages download from PyPI
- **Storage:** Full installation ~3-5GB

---

_Reference: dependency_audit.md, ISSUES_FOUND.md (Issue #1)_  
_Generated: October 4, 2025_
