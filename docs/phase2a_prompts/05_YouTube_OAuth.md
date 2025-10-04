# 🔐 PROMPT #5: YouTube OAuth Setup

## Phase 2A - Critical Issue Resolution

**Reference Code:** `[REF:PROMPT-005]`  
**Complexity:** 🔥 High  
**Estimated Time:** 30-60 minutes  
**Prerequisites:** PROMPT #1-4 complete  
**Note:** Can be skipped initially and configured later

---

## 🎯 OBJECTIVE

Configure YouTube Data API v3 OAuth 2.0 credentials to enable automated video uploads to YouTube channels.

**Setup Requirements:**

- Google Cloud Project
- YouTube Data API v3 enabled
- OAuth 2.0 credentials configured
- Authorized redirect URIs set
- Test authentication flow

---

## 📋 COPILOT PROMPT

````
GITHUB COPILOT DIRECTIVE: YOUTUBE OAUTH CONFIGURATION
[REF:PROMPT-005]

CONTEXT:
- Project: Faceless YouTube Automation Platform v2.0
- Phase: 2A - Critical Issue Resolution
- Task: Setup YouTube Data API OAuth 2.0
- Current: client_secrets.json exists but not validated

CURRENT STATE:
Diagnostic shows:
✅ YouTube client secrets file found
⚠️ Credentials validity: UNKNOWN
⚠️ OAuth flow setup: NOT TESTED

Impact: YouTube upload functionality not verified

TASK:
1. Access Google Cloud Console
2. Create/verify Google Cloud Project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Download client_secrets.json
6. Configure authorized redirect URIs
7. Test authentication flow
8. Handle initial OAuth consent

SPECIFIC ACTIONS:

Step 1: Access Google Cloud Console
1. Go to https://console.cloud.google.com/
2. Sign in with Google account (must own/manage YouTube channel)
3. If no project exists, create new project

Step 2: Create New Project (if needed)
1. Click project dropdown at top
2. Click "New Project"
3. Project name: "Faceless YouTube Automation"
4. Organization: (leave default or select)
5. Click "Create"
6. Wait for project creation (30-60 seconds)
7. Select the new project

Step 3: Enable YouTube Data API v3
1. Go to "APIs & Services" → "Library"
2. Search: "YouTube Data API v3"
3. Click on result
4. Click "Enable" button
5. Wait for API to be enabled

Step 4: Configure OAuth Consent Screen
1. Go to "APIs & Services" → "OAuth consent screen"
2. User Type: Select "External" (unless have Google Workspace)
3. Click "Create"
4. Fill out required fields:
   - App name: "Faceless YouTube Automation"
   - User support email: (your email)
   - Developer contact: (your email)
5. Click "Save and Continue"
6. Scopes: Add these YouTube scopes:
   - https://www.googleapis.com/auth/youtube.upload
   - https://www.googleapis.com/auth/youtube
7. Click "Save and Continue"
8. Test users: Add your Google email
9. Click "Save and Continue"
10. Review and click "Back to Dashboard"

Step 5: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "+ Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Faceless YouTube Desktop Client"
5. Click "Create"
6. Download JSON file
7. Click "Download JSON" button
8. Save file as "client_secrets.json" in project root

Step 6: Verify client_secrets.json Format
File should look like:
```json
{
  "installed": {
    "client_id": "xxxxx.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-secret",
    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
  }
}
````

Step 7: Test OAuth Flow
Execute in terminal:

```powershell
# Test authentication
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

if os.path.exists('client_secrets.json'):
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES
    )
    credentials = flow.run_local_server(port=8080)
    print('✅ OAuth flow successful!')
    print(f'Access token: {credentials.token[:20]}...')
else:
    print('❌ client_secrets.json not found')
"
```

Expected: Browser opens, you authorize, script prints success

Step 8: Store Token for Future Use
After first auth, token.json will be created automatically.
Keep this file secure - it contains your authorization.

Step 9: Test YouTube Upload Function
Execute in terminal:

```powershell
python -c "from src.services.youtube_uploader import YouTubeUploader; uploader = YouTubeUploader(); print('✅ YouTube uploader initialized')"
```

Step 10: Run Final Diagnostic

```powershell
python scripts/diagnostics.py
```

All tests should now pass

REQUIREMENTS:

- Google account with YouTube channel
- Google Cloud Console access
- Browser for OAuth flow
- google-api-python-client installed (from PROMPT #1)
- google-auth-oauthlib installed (from PROMPT #1)

SECURITY NOTES:

- client_secrets.json contains sensitive data (don't commit)
- token.json contains access token (don't share)
- Both should be in .gitignore (already configured)
- OAuth tokens expire and need refresh
- Only authorize on trusted computers

ERROR HANDLING:

- If API not enabled, enable in Cloud Console
- If quota exceeded, wait 24 hours or request increase
- If redirect URI mismatch, add URI to OAuth client settings
- If consent screen error, verify email and test user added

DELIVERABLES:

1. Google Cloud Project created with YouTube API enabled
2. OAuth consent screen configured
3. OAuth 2.0 credentials created and downloaded
4. client_secrets.json in project root
5. Successful OAuth authentication test
6. token.json generated
7. YouTube uploader imports successfully

SUCCESS CRITERIA:
✅ YouTube Data API v3 enabled in Cloud Console
✅ OAuth consent screen configured
✅ client_secrets.json downloaded and placed in project root
✅ OAuth authentication test passes (browser flow works)
✅ token.json created
✅ YouTubeUploader imports without errors
✅ Diagnostic shows YouTube OAuth: CONFIGURED

OPTIONAL: Test with Actual Upload
If you want to test full upload flow (optional):

```powershell
# Create a test video file first
python -c "
from src.services.youtube_uploader import YouTubeUploader
uploader = YouTubeUploader()
# uploader.upload_video('path/to/test.mp4', 'Test Title', 'Test Description')
print('✅ Upload test ready (uncomment to actually upload)')
"
```

NEXT STEP:
Once complete, proceed to PROMPT #6 (System Verification)

```

---

## 🔍 DETAILED VISUAL GUIDE

### Google Cloud Console Setup

#### 1. Create Project

**Navigate to:** https://console.cloud.google.com/

<img src="..." alt="Create Project Screenshot" width="600">

1. Click project dropdown (top left)
2. Click "NEW PROJECT"
3. Enter name: "Faceless YouTube Automation"
4. Click "CREATE"

#### 2. Enable YouTube Data API

**Navigate to:** APIs & Services → Library

1. Search: "YouTube Data API v3"
2. Click first result
3. Click "ENABLE" button

#### 3. Configure OAuth Consent Screen

**Navigate to:** APIs & Services → OAuth consent screen

**App Information:**
```

App name: Faceless YouTube Automation
User support email: your-email@gmail.com
App logo: (optional)

```

**App Domain:**
```

Application home page: http://localhost:8000

```

**Authorized Domains:**
```

localhost

```

**Developer Contact:**
```

your-email@gmail.com

````

**Scopes:**
Add these YouTube scopes:
- `../auth/youtube`
- `../auth/youtube.upload`

**Test Users:**
Add your Google email address

#### 4. Create OAuth Credentials

**Navigate to:** APIs & Services → Credentials

1. Click "+ CREATE CREDENTIALS"
2. Select "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Faceless YouTube Desktop Client"
5. Click "CREATE"
6. Click "DOWNLOAD JSON"
7. Rename file to `client_secrets.json`
8. Move to project root: `C:\FacelessYouTube\`

---

## ⚠️ TROUBLESHOOTING

### Issue: "API has not been used in project..."

**Solution:**
Wait 2-3 minutes after enabling API, then retry.

### Issue: "Redirect URI mismatch"

**Solution:**
Add authorized redirect URIs in OAuth client settings:
- `http://localhost:8080/`
- `http://localhost`
- `urn:ietf:wg:oauth:2.0:oob`

### Issue: "Access blocked: This app's request is invalid"

**Solution:**
Verify OAuth consent screen is fully configured with:
- App name
- Support email
- Developer contact
- At least one scope added

### Issue: Browser doesn't open during auth

**Manual Auth:**
```powershell
# If run_local_server fails, use console flow:
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secrets.json', SCOPES
)
credentials = flow.run_console()
print('✅ Authorized!')
"
````

Follow the URL printed, authorize, paste code back.

### Issue: "invalid_grant" error

**Solution:**
Token expired or invalid. Delete `token.json` and re-authenticate:

```powershell
Remove-Item token.json
# Then run auth test again
```

### Issue: Quota exceeded

**Check Quota:**

1. Go to Cloud Console → APIs & Services → Dashboard
2. Click "YouTube Data API v3"
3. View "Quotas" tab

**Solution:**

- Free quota: 10,000 units/day
- Upload costs: 1,600 units
- Request quota increase if needed

---

## ✅ SUCCESS VERIFICATION

### Checklist

- [ ] Google Cloud Project created
- [ ] YouTube Data API v3 enabled
- [ ] OAuth consent screen configured
- [ ] OAuth credentials created
- [ ] client_secrets.json downloaded
- [ ] client_secrets.json in project root
- [ ] OAuth authentication test passes
- [ ] token.json generated
- [ ] YouTube uploader imports successfully

### Complete Authentication Test

```powershell
# Full OAuth flow test
python -c "
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

print('🔐 Testing YouTube OAuth...')

# Check files exist
if not os.path.exists('client_secrets.json'):
    print('❌ client_secrets.json not found')
    exit(1)

print('✅ client_secrets.json found')

# Test auth flow
try:
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES
    )
    credentials = flow.run_local_server(port=8080)
    print('✅ OAuth authentication successful')

    # Test API connection
    youtube = build('youtube', 'v3', credentials=credentials)
    print('✅ YouTube API client built')

    # Get channel info
    request = youtube.channels().list(part='snippet', mine=True)
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        channel_name = response['items'][0]['snippet']['title']
        print(f'✅ Connected to channel: {channel_name}')
        print('\n🎉 YOUTUBE OAUTH FULLY CONFIGURED!')
    else:
        print('⚠️ No channel found for this account')

except Exception as e:
    print(f'❌ Error: {e}')
"
```

**Expected Output:**

```
🔐 Testing YouTube OAuth...
✅ client_secrets.json found
✅ OAuth authentication successful
✅ YouTube API client built
✅ Connected to channel: Your Channel Name

🎉 YOUTUBE OAUTH FULLY CONFIGURED!
```

---

## 📊 BEFORE & AFTER

### Before

```
YouTube OAuth: UNCONFIGURED ⚠️
✅ client_secrets.json exists
⚠️ Credentials validity: UNKNOWN
⚠️ OAuth flow: NOT TESTED

Status: Upload functionality UNKNOWN
```

### After

```
YouTube OAuth: CONFIGURED ✅
✅ client_secrets.json configured
✅ OAuth credentials validated
✅ token.json generated
✅ API connection successful
✅ Channel access confirmed

Status: Upload functionality READY
```

---

## 🎯 NEXT STEPS

Once YouTube OAuth is configured:

1. **Save your credentials securely** (password manager)

2. **Proceed to PROMPT #6:** [System Verification](06_System_Verification.md)

3. **Mark this task complete** in your checklist

**Status Update:**

- ✅ Critical Issue #1: RESOLVED
- ✅ Critical Issue #2: RESOLVED
- ✅ Critical Issue #3: RESOLVED
- ✅ Critical Issue #4: RESOLVED
- ✅ Critical Issue #5: RESOLVED (YouTube OAuth)
- ⏳ Critical Issue #6: Next (Final Verification)

---

## 📝 IMPORTANT NOTES

### File Security

**DO NOT COMMIT:**

- `client_secrets.json` - OAuth credentials
- `token.json` - Access/refresh tokens
- `token.pickle` - Serialized credentials

These are already in `.gitignore`.

### Token Expiration

- Access tokens expire after 1 hour
- Refresh tokens last indefinitely (until revoked)
- Library automatically refreshes tokens
- If refresh fails, delete `token.json` and re-auth

### Production Deployment

For production, consider:

- Service account credentials (for server-to-server)
- Secure secrets management (Azure Key Vault, AWS Secrets)
- Token encryption at rest
- Audit logging of API calls

### Rate Limits

**YouTube Data API v3 Quota:**

- Default: 10,000 units/day
- Video upload: 1,600 units
- ~6 uploads per day with default quota
- Request increase: up to 1,000,000 units/day

---

## 🆘 SKIP OPTION

**If YouTube uploads not needed immediately:**

You can skip this prompt and proceed to PROMPT #6. YouTube functionality will be disabled but the rest of the system will work.

To skip:

1. Comment out YouTube tests in `scripts/diagnostics.py`
2. Don't run YouTube upload functions
3. Return to this prompt when ready for uploads

---

_Reference: ISSUES_FOUND.md (Issue #6), Google Cloud Console documentation_  
_Generated: October 4, 2025_
