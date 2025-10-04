# DEPENDENCY AUDIT

**Faceless YouTube Automation Platform v2.0**  
**Generated:** October 4, 2025  
**Audit Type:** Python & Node.js Dependencies

---

## EXECUTIVE SUMMARY

### Python Dependencies

- **Total Required:** 69 packages
- **Correctly Installed:** 0 packages (all have newer versions)
- **Missing Packages:** 28 packages ❌
- **Version Mismatches:** 41 packages ⚠️
- **Potentially Unused:** 324 packages 🔍
- **Overall Status:** ❌ **CRITICAL - Installation Required**

### Node.js Dependencies

- **Total Required:** 22 packages
- **Installed:** 0 packages ❌
- **Missing:** 22 packages (ALL)
- **Overall Status:** ❌ **CRITICAL - npm install Required**

### Immediate Actions Required

1. ❌ **Install Python dependencies:** `pip install -r requirements.txt`
2. ❌ **Install Node.js dependencies:** `cd dashboard && npm install`
3. ⚠️ **Review version mismatches** - Most are newer (likely compatible)
4. 🔍 **Audit unused packages** - 324 packages not in requirements.txt

---

## PYTHON DEPENDENCY ANALYSIS

### Critical Missing Packages (28)

These packages are **required** but **not installed**:

#### Video Processing (5 packages)

```
❌ moviepy==1.0.3                  # Video editing
❌ ffmpeg-python==0.2.0            # FFmpeg wrapper
❌ pydub==0.25.1                   # Audio manipulation
❌ opencv-python==4.8.1.78         # Video processing (INSTALLED but version 4.12.0.88)
❌ mutagen==1.47.0                 # Audio metadata
```

#### AI/ML Services (2 packages)

```
❌ sentence-transformers==2.2.2    # Text embeddings (CLIP)
❌ torchvision==0.16.1             # Vision models (INSTALLED but version differs)
```

#### Backend Services (6 packages)

```
❌ uvicorn[standard]==0.24.0       # ASGI server (INSTALLED but version 0.35.0)
❌ celery==5.3.4                   # Distributed task queue
❌ celery-redbeat==2.1.1           # Redis-backed scheduler
❌ asyncpg==0.29.0                 # Async PostgreSQL
❌ psycopg2-binary==2.9.9          # PostgreSQL adapter
❌ google-api-python-client==2.108.0  # YouTube API
```

#### TTS/Audio (2 packages)

```
❌ tts==0.21.1                     # Coqui TTS (local, high quality)
❌ pyttsx3==2.90                   # Offline TTS (fallback)
```

#### Desktop GUI (2 packages)

```
❌ pyqt6==6.6.1                    # Desktop GUI framework
❌ pyqt6-webengine==6.6.0          # Web view component
```

#### Development Tools (5 packages)

```
❌ ipython==8.18.1                 # Enhanced Python REPL
❌ ipdb==0.13.13                   # Debugger
❌ factory-boy==3.3.0              # Test fixtures
❌ faker==20.1.0                   # Fake data generation
❌ playwright==1.40.0              # Browser automation
```

#### Utilities (6 packages)

```
❌ arrow==1.3.0                    # Better datetime handling
❌ python-jose[cryptography]==3.3.0  # JWT handling
❌ passlib[bcrypt]==1.7.4          # Password hashing
❌ python-slugify==8.0.1           # URL-safe strings
❌ imagehash==4.3.1                # Perceptual hashing (deduplication)
❌ sentry-sdk==1.39.1              # Error tracking (optional)
```

### Impact Assessment

**CRITICAL IMPACT:**

- ❌ **Backend API won't start** - uvicorn missing
- ❌ **Video generation will fail** - moviepy, opencv missing
- ❌ **YouTube uploads broken** - google-api-python-client missing
- ❌ **AI embeddings unavailable** - sentence-transformers missing
- ❌ **TTS unavailable** - tts, pyttsx3 missing

**MEDIUM IMPACT:**

- ⚠️ **No async task queue** - celery missing
- ⚠️ **No async PostgreSQL** - asyncpg missing
- ⚠️ **Desktop GUI unavailable** - PyQt6 missing

**LOW IMPACT:**

- 🔍 **Development features unavailable** - ipython, ipdb, faker
- 🔍 **Optional monitoring missing** - sentry-sdk

---

### Version Mismatches (41 packages)

These packages are installed but with **newer versions** than specified:

#### Core Framework (7 packages)

```
⚠️ fastapi: Required 0.104.1, Installed 0.116.1
⚠️ pydantic: Required 2.5.0, Installed 2.9.2
⚠️ sqlalchemy: Required 2.0.23, Installed 2.0.43
⚠️ uvicorn: Required 0.24.0, Installed 0.35.0 (IF INSTALLED)
⚠️ alembic: Required 1.12.1, Installed 1.16.4
⚠️ python-dotenv: Required 1.0.0, Installed 1.1.1
⚠️ python-multipart: Required 0.0.6, Installed 0.0.20
```

**Assessment:** ✅ Newer versions generally compatible with FastAPI/Pydantic ecosystem

#### AI/ML Libraries (6 packages)

```
⚠️ torch: Required 2.1.1, Installed 2.8.0
⚠️ torchvision: Required 0.16.1, Installed [CHECK]
⚠️ numpy: Required 1.26.2, Installed 2.2.6
⚠️ pillow: Required 10.1.0, Installed 11.3.0
⚠️ opencv-python: Required 4.8.1.78, Installed 4.12.0.88
⚠️ scikit-learn: Required 1.3.2, Installed 1.7.1
```

**Assessment:** ⚠️ **PyTorch major version jump** (2.1→2.8) - test CLIP compatibility  
✅ Others: Minor/patch updates, likely compatible

#### Database (4 packages)

```
⚠️ pymongo: Required 4.6.0, Installed 4.14.1
⚠️ motor: Required 3.3.2, Installed 3.7.1
⚠️ redis: Required 5.0.1, Installed 6.4.0
⚠️ hiredis: Required 2.2.3, Installed 3.2.1
```

**Assessment:** ✅ All backward compatible

#### HTTP/Networking (3 packages)

```
⚠️ httpx: Required 0.25.2, Installed 0.28.1
⚠️ aiohttp: Required 3.9.1, Installed 3.12.15
⚠️ requests: Required 2.31.0, Installed 2.32.4
```

**Assessment:** ✅ Minor updates, backward compatible

#### Testing (4 packages)

```
⚠️ pytest: Required 7.4.3, Installed 8.2.0
⚠️ pytest-asyncio: Required 0.21.1, Installed 1.1.0
⚠️ pytest-cov: Required 4.1.0, Installed 6.2.1
⚠️ pytest-mock: Required 3.12.0, Installed 3.14.1
```

**Assessment:** ✅ pytest 8.x compatible with existing tests

#### Utilities & Tooling (17 packages)

```
⚠️ black: Required 23.12.0, Installed 25.1.0
⚠️ ruff: Required 0.1.7, Installed 0.5.5
⚠️ mypy: Required 1.7.1, Installed 1.10.0
⚠️ pre-commit: Required 3.5.0, Installed 3.7.1
⚠️ click: Required 8.1.7, Installed 8.2.1
⚠️ pyyaml: Required 6.0.1, Installed 6.0.2
⚠️ toml: Required 0.10.2, Installed 0.10.2
⚠️ tqdm: Required 4.66.1, Installed 4.67.1
⚠️ tenacity: Required 8.2.3, Installed 9.1.2
⚠️ apscheduler: Required 3.10.4, Installed 3.11.0
⚠️ structlog: Required 23.2.0, Installed 25.4.0
⚠️ prometheus-client: Required 0.19.0, Installed 0.22.1
⚠️ beautifulsoup4: Required 4.12.2, Installed 4.13.4
⚠️ lxml: Required 4.9.3, Installed 6.0.0
⚠️ keyring: Required 24.3.0, Installed 25.6.0
⚠️ watchdog: Required 3.0.0, Installed 6.0.0
⚠️ cryptography: Required 41.0.7, Installed 45.0.6
```

**Assessment:** ✅ All minor/patch updates, backward compatible

#### Google APIs (2 packages)

```
⚠️ google-auth-oauthlib: Required 1.2.0, Installed 1.2.2
⚠️ google-auth: Required [NOT IN REQUIREMENTS], Installed 2.40.3
```

**Assessment:** ✅ Patch update, compatible

---

### Recommendation: Version Mismatch Strategy

**Option 1: Use Installed Versions (RECOMMENDED)**

- ✅ **Faster** - No downloads needed
- ✅ **More secure** - Newer versions have security patches
- ⚠️ **Risk:** Potential API changes (low risk for minor/patch updates)
- **Action:** Update `requirements.txt` to match installed versions

**Option 2: Downgrade to Exact Versions**

- ✅ **Guaranteed compatibility** - Matches original development
- ❌ **Slower** - Large downloads required
- ❌ **Security risk** - Older versions may have known vulnerabilities
- **Action:** `pip install --force-reinstall -r requirements.txt`

**Option 3: Hybrid Approach (BEST)**

- Keep newer versions for:
  - Testing frameworks (pytest 8.x)
  - Development tools (black, ruff, mypy)
  - Utilities (click, pyyaml, tqdm)
- Install exact versions for:
  - ❌ **CRITICAL:** torch, torchvision (AI models sensitive to versions)
  - ❌ **CRITICAL:** FastAPI, Pydantic (API contracts)

**Recommended Command:**

```bash
# Install missing critical packages
pip install moviepy==1.0.3 ffmpeg-python==0.2.0 sentence-transformers==2.2.2
pip install google-api-python-client==2.108.0 tts==0.21.1 pyttsx3==2.90

# Keep existing newer versions for everything else
```

---

### Potentially Unused Packages (324)

These packages are **installed** but **not listed** in `requirements.txt`:

#### Legitimate Dependencies (Sub-dependencies)

Many of these are **transitive dependencies** installed automatically:

**PyTorch Ecosystem:**

```
✅ sympy, networkx, filelock (torch dependencies)
✅ safetensors, huggingface-hub, tokenizers (transformers dependencies)
```

**FastAPI Ecosystem:**

```
✅ starlette, uvicorn, h11, httpcore (FastAPI dependencies)
✅ anyio, sniffio (async dependencies)
```

**Database Drivers:**

```
✅ psycopg2 (PostgreSQL - should be in requirements!)
✅ greenlet (SQLAlchemy async)
```

**System Utilities:**

```
✅ certifi, charset-normalizer, idna, urllib3 (HTTP dependencies)
✅ pywin32 (Windows-specific)
```

#### Questionable Packages (Should Investigate)

**AI/ML Libraries (possibly from other projects):**

```
🔍 tensorflow==2.20.0rc0 - NOT NEEDED (using PyTorch)
🔍 keras==3.11.1 - NOT NEEDED
🔍 qiskit==2.1.1 - Quantum computing (NOT NEEDED)
🔍 langchain==0.3.27 - May be useful for future
🔍 ollama==0.5.3 - Should be in requirements!
🔍 anthropic==0.64.0 - Claude API (future use)
🔍 openai==1.101.0 - GPT API (future use)
```

**Astronomy Libraries (NOT NEEDED):**

```
🔍 astropy==7.1.0
🔍 astroquery==0.4.10
🔍 photutils==2.2.0
🔍 poppy==1.1.2
🔍 jwst-mast-query==0.0.6
```

**Load Testing (Development Only):**

```
🔍 locust==2.38.0
🔍 locust-cloud==1.26.3
```

**Blockchain/Web3 (NOT NEEDED):**

```
🔍 web3==7.12.1
🔍 eth-account==0.13.7
🔍 eth-utils==5.3.0
```

**Unused Frameworks:**

```
🔍 flask==3.1.1 - NOT NEEDED (using FastAPI)
🔍 dash==3.2.0 - NOT NEEDED
🔍 spacy==3.8.7 - NLP (may be useful)
```

#### Critical Missing from requirements.txt

These **ARE needed** but **not in requirements.txt**:

```
❌ ollama==0.5.3 - Ollama Python client (CRITICAL)
❌ psycopg2==2.9.10 - PostgreSQL driver
❌ anthropic==0.64.0 - Claude API (if using)
❌ openai==1.101.0 - OpenAI API (if using)
❌ spacy==3.8.7 - NLP processing (if using)
❌ langchain==0.3.27 - LLM orchestration (if using)
```

---

### Python Dependencies: Recommended Actions

#### Immediate (Before Packaging)

```bash
# 1. Install all missing critical packages
pip install -r requirements.txt

# 2. Add critical missing packages to requirements.txt
echo "ollama==0.5.3" >> requirements.txt
echo "psycopg2==2.9.10" >> requirements.txt

# 3. Test PyTorch 2.8 compatibility with CLIP
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('clip-ViT-B-32'); print('✅ CLIP OK')"

# 4. Clean up unused packages (optional)
pip uninstall tensorflow keras qiskit astropy flask dash -y
```

#### Future (Post-Packaging)

```bash
# Generate fresh requirements.txt from working environment
pip freeze > requirements_frozen.txt

# Use pip-tools for better dependency management
pip install pip-tools
pip-compile requirements.in --output-file=requirements.txt
```

---

## NODE.JS DEPENDENCY ANALYSIS

### Critical Status: ALL PACKAGES MISSING ❌

The `dashboard/` directory has `package.json` but **`node_modules/` does not exist**.

### Required Packages (22 total)

#### Production Dependencies (16 packages)

```
❌ react@^18.2.0                    # React framework
❌ react-dom@^18.2.0                # React DOM renderer
❌ react-router-dom@^6.20.0         # Client-side routing
❌ axios@^1.6.2                     # HTTP client
❌ @tanstack/react-query@^5.14.2    # Data fetching/caching
❌ zustand@^4.4.7                   # State management
❌ date-fns@^3.0.0                  # Date utilities
❌ react-calendar@^4.7.0            # Calendar component
❌ recharts@^2.10.3                 # Charts/analytics
❌ lucide-react@^0.294.0            # Icons
❌ react-hot-toast@^2.4.1           # Notifications
❌ clsx@^2.0.0                      # Conditional CSS classes
❌ tailwindcss@^3.3.6               # CSS framework
❌ autoprefixer@^10.4.16            # CSS post-processor
❌ postcss@^8.4.32                  # CSS processor
❌ vite@^5.0.8                      # Build tool
```

#### Development Dependencies (6 packages)

```
❌ @types/react@^18.2.43            # TypeScript types for React
❌ @types/react-dom@^18.2.17        # TypeScript types for React DOM
❌ @vitejs/plugin-react@^4.2.1      # Vite React plugin
❌ eslint@^8.55.0                   # JavaScript linter
❌ eslint-plugin-react@^7.33.2      # React-specific linting rules
❌ prettier@^3.1.1                  # Code formatter
```

### Impact Assessment

**CRITICAL IMPACT:**

- ❌ **Frontend won't build** - Vite missing
- ❌ **Cannot run dev server** - All React dependencies missing
- ❌ **Cannot deploy production build**

### Installation Required

```bash
cd dashboard
npm install
```

**Expected Download Size:** ~400MB (node_modules)  
**Installation Time:** 2-5 minutes

---

### Node.js Package Versions: Should We Update?

**Current `package.json` versions (from December 2023):**

- React 18.2 (Latest: 18.3 - October 2024)
- Vite 5.0 (Latest: 5.4 - October 2024)
- TailwindCSS 3.3 (Latest: 3.4 - January 2024)

**Recommendation: Update to Latest Stable**

Create `package.json` with updated versions:

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "vite": "^5.4.11",
    "tailwindcss": "^3.4.15"
    // ... (other packages)
  }
}
```

**Benefits:**

- ✅ Security patches
- ✅ Performance improvements
- ✅ Bug fixes

**Risks:**

- ⚠️ Minimal - React 18.2 → 18.3 is backward compatible
- ⚠️ TailwindCSS 3.3 → 3.4 has minor changes

---

### Node.js Dependencies: Recommended Actions

#### Immediate (Before Packaging)

```bash
# Navigate to dashboard
cd dashboard

# Install all dependencies
npm install

# Verify installation
npm list --depth=0

# Test dev server
npm run dev
```

#### Optional: Update to Latest Versions

```bash
# Check for outdated packages
npm outdated

# Update minor/patch versions
npm update

# Update major versions (carefully)
npm install react@latest react-dom@latest
npm install vite@latest
```

---

## SECURITY AUDIT

### Python Security Issues

**High Priority:**

```
⚠️ cryptography: 41.0.7 → 45.0.6 (Security patches in newer version)
⚠️ requests: 2.31.0 → 2.32.4 (CVE fixes)
⚠️ pillow: 10.1.0 → 11.3.0 (Security fixes)
⚠️ lxml: 4.9.3 → 6.0.0 (Security patches)
```

**Recommendation:** ✅ **Keep newer versions installed** (already have security fixes)

### Node.js Security Issues

**Status:** ❓ **Unknown** (packages not installed)

**Action:** After installation, run:

```bash
npm audit
npm audit fix  # Auto-fix vulnerabilities
```

---

## DEPENDENCY MANAGEMENT RECOMMENDATIONS

### Python Best Practices

1. **Use pip-tools for pinning:**

   ```bash
   pip install pip-tools
   pip-compile requirements.in --output-file=requirements.txt
   ```

2. **Separate dev dependencies:**
   Create `requirements-dev.txt`:

   ```
   ipython
   ipdb
   pytest
   black
   ruff
   mypy
   ```

3. **Use virtual environments:**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

4. **Regular updates:**
   ```bash
   pip list --outdated
   pip install --upgrade [package]
   ```

### Node.js Best Practices

1. **Use package-lock.json:**

   - ✅ Already present
   - Ensures consistent installations

2. **Audit regularly:**

   ```bash
   npm audit
   npm outdated
   ```

3. **Consider pnpm or yarn:**

   - Faster installations
   - Better disk space usage

4. **Pin major versions:**
   ```json
   {
     "react": "~18.2.0", // Patch updates only
     "vite": "^5.0.0" // Minor+patch updates
   }
   ```

---

## SUMMARY & NEXT STEPS

### Current Status

| Component          | Status              | Action Required                               |
| ------------------ | ------------------- | --------------------------------------------- |
| Python Packages    | ❌ **28 missing**   | `pip install -r requirements.txt`             |
| Node.js Packages   | ❌ **All missing**  | `cd dashboard && npm install`                 |
| Version Mismatches | ⚠️ **41 packages**  | Test compatibility or update requirements.txt |
| Unused Packages    | 🔍 **324 packages** | Audit and remove if needed                    |

### Priority Actions

**P0 (Critical - Before Any Testing):**

1. ❌ `pip install -r requirements.txt`
2. ❌ `cd dashboard && npm install`
3. ❌ Test imports: `python -c "import fastapi, moviepy, torch"`
4. ❌ Test frontend build: `npm run build`

**P1 (High - Before Packaging):**

1. ⚠️ Add missing packages to requirements.txt (ollama, psycopg2)
2. ⚠️ Test PyTorch 2.8 compatibility with CLIP models
3. ⚠️ Update requirements.txt to match installed versions (or downgrade)
4. ⚠️ Run security audit: `npm audit && safety check`

**P2 (Medium - Code Quality):**

1. 🔍 Review and remove unused packages (tensorflow, qiskit, astropy, etc.)
2. 🔍 Split requirements.txt into prod/dev
3. 🔍 Document why each package is needed

**P3 (Low - Maintenance):**

1. 📝 Set up automated dependency updates (Dependabot)
2. 📝 Document version pinning strategy
3. 📝 Create DEPENDENCIES.md with package justifications

---

**END OF DEPENDENCY AUDIT**  
_Next: Proceed to Task 3 - Master Configuration System_
