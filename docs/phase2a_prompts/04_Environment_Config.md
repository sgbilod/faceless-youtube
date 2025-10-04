# ⚙️ PROMPT #4: Environment Configuration

## Phase 2A - Critical Issue Resolution

**Reference Code:** `[REF:PROMPT-004]`  
**Complexity:** ⚡ Low  
**Estimated Time:** 15-30 minutes  
**Prerequisites:** PROMPT #1, #2, #3 complete

---

## 🎯 OBJECTIVE

Configure all environment variables in `.env` file including database credentials, API keys, and application settings.

**Configuration Areas:**

- Database credentials (PostgreSQL, MongoDB, Redis)
- API keys (Pexels, Pixabay, ElevenLabs, OpenAI)
- Application settings (debug mode, ports, paths)
- YouTube OAuth (client secrets)

---

## 📋 COPILOT PROMPT

````
GITHUB COPILOT DIRECTIVE: ENVIRONMENT CONFIGURATION SETUP
[REF:PROMPT-004]

CONTEXT:
- Project: Faceless YouTube Automation Platform v2.0
- Phase: 2A - Critical Issue Resolution
- Task: Complete .env configuration
- Reference: .env.example template

CURRENT STATE:
Diagnostic warnings:
⚠️ PostgreSQL password not set
⚠️ Pexels API key not set (video assets limited)
⚠️ Pixabay API key not set (video assets limited)
⚠️ Debug mode enabled (should be false for production)

Impact: Limited functionality, potential security issues, reduced asset sources

TASK:
1. Copy .env.example to .env (if not exists)
2. Configure database credentials
3. Obtain and set API keys (Pexels, Pixabay)
4. Configure application settings
5. Set production-ready values
6. Verify configuration loads correctly
7. Test API connections

SPECIFIC ACTIONS:

Step 1: Create .env File
Execute in terminal:
```powershell
# Check if .env exists
if (!(Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "✅ Created .env from template"
} else {
    Write-Host "ℹ️ .env already exists"
}
````

Step 2: Configure Database Section
Open .env in VS Code and update:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=faceless_youtube
DB_USER=postgres
DB_PASSWORD=your_actual_password_here  # ← UPDATE THIS

# MongoDB
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB=faceless_youtube

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Step 3: Get Pexels API Key

1. Go to https://www.pexels.com/api/
2. Click "Get Started" or "Sign Up"
3. Verify email
4. Go to "Your API Key" section
5. Copy the API key
6. Add to .env:

```env
PEXELS_API_KEY=your_pexels_api_key_here
```

Step 4: Get Pixabay API Key

1. Go to https://pixabay.com/api/docs/
2. Sign up for free account
3. Navigate to API documentation
4. Find your API key
5. Add to .env:

```env
PIXABAY_API_KEY=your_pixabay_api_key_here
```

Step 5: Configure Application Settings
Update in .env:

```env
# Application
DEBUG=false  # ← IMPORTANT: Set to false for production
APP_NAME=Faceless YouTube Automation
APP_VERSION=2.0.0
ENVIRONMENT=production  # or 'development'

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
FRONTEND_PORT=3000
```

Step 6: Configure AI Services (Optional)
If using external AI services:

```env
# OpenAI (optional)
OPENAI_API_KEY=your_openai_key_here

# ElevenLabs (optional)
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
```

Step 7: Verify Configuration
Execute in terminal:

```powershell
python -c "from src.config.master_config import MasterConfig; config = MasterConfig(); config.print_config()"
```

Should show all configurations loaded without errors

Step 8: Test API Keys
Execute in terminal:

```powershell
# Test Pexels
python -c "
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('PEXELS_API_KEY')
if api_key:
    response = httpx.get(
        'https://api.pexels.com/v1/search?query=nature&per_page=1',
        headers={'Authorization': api_key}
    )
    if response.status_code == 200:
        print('✅ Pexels API key valid')
    else:
        print(f'❌ Pexels API error: {response.status_code}')
else:
    print('⚠️ Pexels API key not set')
"

# Test Pixabay (similar pattern)
```

Step 9: Run Full Diagnostic

```powershell
python scripts/diagnostics.py
```

Check that warnings are resolved

REQUIREMENTS:

- .env.example file exists (reference template)
- Free API accounts (Pexels, Pixabay)
- Email addresses for account verification
- Secure password manager for storing credentials

SECURITY NOTES:

- Never commit .env to git (already in .gitignore)
- Use strong passwords for databases
- Keep API keys secret
- Don't share .env file
- Use environment variables for production deployment

ERROR HANDLING:

- If API key test fails, verify key was copied correctly
- If config loading fails, check .env syntax (no spaces around =)
- If database connection fails, verify credentials match database setup
- If file not found, ensure .env is in project root

DELIVERABLES:

1. Complete .env file with all required values
2. Valid API keys for Pexels and Pixabay
3. Database credentials configured
4. DEBUG mode set to false
5. Configuration loads without errors
6. Diagnostic warnings resolved

SUCCESS CRITERIA:
✅ .env file exists in project root
✅ All database credentials are set
✅ Pexels API key is valid
✅ Pixabay API key is valid
✅ DEBUG=false for production
✅ Configuration loads successfully
✅ No configuration warnings in diagnostics

NEXT STEP:
Once complete, proceed to PROMPT #5 (YouTube OAuth Setup)

````

---

## 🔍 DETAILED INSTRUCTIONS

### Step-by-Step .env Setup

#### 1. Create .env File

```powershell
# PowerShell
Copy-Item .env.example .env

# Or manually in VS Code:
# 1. Open .env.example
# 2. File → Save As → .env
````

#### 2. Database Configuration

Update these sections with your actual credentials:

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=faceless_youtube
DB_USER=postgres
DB_PASSWORD=YourSecurePassword123!  # ← From PROMPT #3

# MongoDB
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB=faceless_youtube

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

#### 3. Get Pexels API Key

**Visual Guide:**

1. Visit: https://www.pexels.com/api/
2. Click: "Get Started" button
3. Sign up with email
4. Verify email (check inbox)
5. Login and go to: https://www.pexels.com/api/new/
6. API key will be displayed
7. Copy the key (looks like: `abc123def456ghi789...`)

**Add to .env:**

```env
PEXELS_API_KEY=abc123def456ghi789
```

**Rate Limits:** 200 requests/hour (free tier)

#### 4. Get Pixabay API Key

**Visual Guide:**

1. Visit: https://pixabay.com/api/docs/
2. Click: "Sign Up"
3. Create free account
4. Navigate to: https://pixabay.com/api/docs/
5. Find "Your API Key" section
6. Copy the key (looks like: `12345678-abc...`)

**Add to .env:**

```env
PIXABAY_API_KEY=12345678-abc
```

**Rate Limits:** 5000 requests/hour (free tier)

#### 5. Application Settings

```env
# IMPORTANT: Set DEBUG to false
DEBUG=false

# Application Info
APP_NAME=Faceless YouTube Automation
APP_VERSION=2.0.0
ENVIRONMENT=production

# Server Ports
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3000

# Paths (use forward slashes even on Windows)
PROJECT_ROOT=C:/FacelessYouTube
OUTPUT_DIR=C:/FacelessYouTube/output_videos
ASSETS_DIR=C:/FacelessYouTube/assets
```

---

## ⚠️ TROUBLESHOOTING

### Issue: Configuration not loading

**Check syntax:**

```env
# CORRECT
API_KEY=abc123

# WRONG (no spaces)
API_KEY = abc123

# WRONG (no quotes needed)
API_KEY="abc123"
```

### Issue: API key invalid

**Test manually:**

```powershell
# Test Pexels
curl -H "Authorization: YOUR_KEY" "https://api.pexels.com/v1/search?query=nature&per_page=1"
```

Expected: JSON response with photos

### Issue: Database connection fails

**Verify credentials:**

```powershell
# Test PostgreSQL connection
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='YOUR_PASSWORD',
    database='postgres'
)
print('✅ Connected')
conn.close()
"
```

### Issue: .env not found

**Check location:**

```powershell
# Must be in project root
ls .env
# Should show: .env

# If not, check current directory
pwd
# Should be: C:\FacelessYouTube
```

---

## ✅ SUCCESS VERIFICATION

### Checklist

- [ ] .env file exists in project root
- [ ] Database credentials set (PostgreSQL, MongoDB, Redis)
- [ ] Pexels API key obtained and set
- [ ] Pixabay API key obtained and set
- [ ] DEBUG mode set to false
- [ ] All paths configured correctly
- [ ] Configuration loads without errors

### Verification Script

```powershell
# Comprehensive configuration test
python -c "
import os
from dotenv import load_dotenv
from src.config.master_config import MasterConfig

# Load configuration
load_dotenv()
config = MasterConfig()

# Check critical values
checks = {
    'DB_PASSWORD': os.getenv('DB_PASSWORD', ''),
    'PEXELS_API_KEY': os.getenv('PEXELS_API_KEY', ''),
    'PIXABAY_API_KEY': os.getenv('PIXABAY_API_KEY', ''),
    'DEBUG': os.getenv('DEBUG', 'true'),
}

print('📋 Configuration Check:')
print(f'✅ PostgreSQL Password: {'SET' if checks['DB_PASSWORD'] else '❌ MISSING'}')
print(f'✅ Pexels API Key: {'SET' if checks['PEXELS_API_KEY'] else '⚠️ MISSING'}')
print(f'✅ Pixabay API Key: {'SET' if checks['PIXABAY_API_KEY'] else '⚠️ MISSING'}')
print(f'✅ DEBUG Mode: {checks['DEBUG']} {'✅' if checks['DEBUG'] == 'false' else '⚠️'}')

if all([checks['DB_PASSWORD'], checks['PEXELS_API_KEY'], checks['PIXABAY_API_KEY']]):
    print('\n🎉 ALL REQUIRED CONFIGURATION SET!')
else:
    print('\n⚠️ Some configuration missing - review above')
"
```

**Expected Output:**

```
📋 Configuration Check:
✅ PostgreSQL Password: SET
✅ Pexels API Key: SET
✅ Pixabay API Key: SET
✅ DEBUG Mode: false ✅

🎉 ALL REQUIRED CONFIGURATION SET!
```

---

## 📊 BEFORE & AFTER

### Before

```
Configuration warnings:
⚠️ PostgreSQL password not set
⚠️ Pexels API key not set (video assets limited)
⚠️ Pixabay API key not set (video assets limited)
⚠️ Debug mode enabled

Impact: Limited asset sources, development mode active
```

### After

```
Configuration: HEALTHY ✅
✅ All database credentials configured
✅ All API keys configured
✅ Production mode enabled (DEBUG=false)
✅ All paths configured

Impact: Full functionality enabled
```

---

## 🎯 NEXT STEPS

Once configuration is complete:

1. **Run final diagnostic:**

   ```powershell
   python scripts/diagnostics.py
   ```

2. **Proceed to PROMPT #5:** [YouTube OAuth Setup](05_YouTube_OAuth.md)

3. **Mark this task complete** in your checklist

**Status Update:**

- ✅ Critical Issue #1: RESOLVED
- ✅ Critical Issue #2: RESOLVED
- ✅ Critical Issue #3: RESOLVED
- ✅ Critical Issue #4: RESOLVED (Environment)
- ⏳ Critical Issue #5: Next (YouTube OAuth)
- ⏳ Critical Issue #6: Pending

---

## 🔒 SECURITY BEST PRACTICES

**Password Requirements:**

- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Use password manager (1Password, LastPass, Bitwarden)
- Different password for each service

**API Key Security:**

- Never commit to git (.gitignore protects .env)
- Never share in chat/email
- Regenerate if accidentally exposed
- Use environment variables in production

**Production Deployment:**

- Use secrets management (Azure Key Vault, AWS Secrets Manager)
- Rotate credentials regularly
- Use read-only database accounts where possible
- Enable audit logging

---

_Reference: ISSUES_FOUND.md (Issues #8-11), .env.example_  
_Generated: October 4, 2025_
