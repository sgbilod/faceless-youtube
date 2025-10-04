# 🔑 API Keys Setup Guide - Prompt #4

## Quick Reference

**You need to get 2 FREE API keys:**

1. ✅ **Pexels API** - 5 minutes
2. ✅ **Pixabay API** - 5 minutes

Both are completely **FREE** with no credit card required!

---

## 🎥 Pexels API Key (Step-by-Step)

### What is Pexels?

Free stock photos and videos. Provides high-quality video clips for your YouTube content.

### Get Your API Key:

1. **Visit Pexels API Page**:

   ```
   https://www.pexels.com/api/
   ```

2. **Click "Get Started"** (top right corner)

3. **Create Free Account**:

   - Enter your email
   - Create password
   - Verify email (check inbox/spam)

4. **Navigate to API Keys**:

   ```
   https://www.pexels.com/api/new/
   ```

   Or: Dashboard → Your Apps → Create New App

5. **Fill Out Application**:

   - **App Name**: `Faceless YouTube Automation`
   - **Description**: `Automated YouTube video content generation`
   - **Website**: `http://localhost` (or your website)
   - **Purpose**: Select "Personal Project"

6. **Submit and Get Key**:

   - Click "Generate API Key"
   - Copy the key (looks like: `abcd1234efgh5678ijkl9012mnop3456`)

7. **Add to .env File**:

   ```bash
   # Open .env in VS Code
   # Find this line:
   PEXELS_API_KEY=

   # Paste your key:
   PEXELS_API_KEY=abcd1234efgh5678ijkl9012mnop3456
   ```

### Pexels API Limits:

- ✅ **Free forever**
- ✅ **200 requests/hour**
- ✅ **20,000 requests/month**
- ✅ No credit card required

---

## 🖼️ Pixabay API Key (Step-by-Step)

### What is Pixabay?

Free stock images and videos. Over 2.7 million high-quality assets.

### Get Your API Key:

1. **Visit Pixabay**:

   ```
   https://pixabay.com/
   ```

2. **Sign Up** (top right):

   - Click "Sign up"
   - Enter email and password
   - OR: Sign up with Google/Facebook

3. **Verify Email**:

   - Check your inbox
   - Click verification link

4. **Go to API Documentation**:

   ```
   https://pixabay.com/api/docs/
   ```

5. **Find Your API Key**:

   - Scroll down to "Your API Key" section
   - Your key is displayed automatically (looks like: `12345678-abcdef1234567890abcdef12`)
   - Click "Copy" button

6. **Add to .env File**:

   ```bash
   # Open .env in VS Code
   # Find this line:
   PIXABAY_API_KEY=

   # Paste your key:
   PIXABAY_API_KEY=12345678-abcdef1234567890abcdef12
   ```

### Pixabay API Limits:

- ✅ **Free forever**
- ✅ **100 requests/minute**
- ✅ **5,000 requests/hour**
- ✅ No credit card required

---

## ✅ Quick Setup Commands

### After Getting Both Keys:

1. **Open .env file** in VS Code

2. **Update these lines**:

   ```bash
   # Replace YOUR_KEY_HERE with actual keys
   PEXELS_API_KEY=your_actual_pexels_key
   PIXABAY_API_KEY=your_actual_pixabay_key
   ```

3. **Save the file** (`Ctrl + S`)

4. **Test the configuration**:

   ```powershell
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()

   pexels = os.getenv('PEXELS_API_KEY')
   pixabay = os.getenv('PIXABAY_API_KEY')

   print(f'Pexels API: {\"✅ Set\" if pexels and pexels != \"\" else \"❌ Missing\"}')
   print(f'Pixabay API: {\"✅ Set\" if pixabay and pixabay != \"\" else \"❌ Missing\"}')

   if pexels and pixabay and pexels != \"\" and pixabay != \"\":
       print(\"\\n🎉 All API keys configured successfully!\")
   else:
       print(\"\\n⚠️  Please add missing API keys to .env file\")
   "
   ```

---

## 🔒 Security Reminders

### DO:

- ✅ Keep API keys in `.env` file only
- ✅ Never commit `.env` to git
- ✅ Use different keys for different projects
- ✅ Regenerate keys if accidentally exposed

### DON'T:

- ❌ Share keys publicly
- ❌ Commit keys to GitHub
- ❌ Hardcode keys in source files
- ❌ Share keys via email/chat

---

## 🚨 Troubleshooting

### "API key not found"

```powershell
# Check if .env file is in correct location
Get-Content C:\FacelessYouTube\.env | Select-String "PEXELS_API_KEY"
```

### "Invalid API key"

- Make sure you copied the entire key
- Check for extra spaces before/after key
- Verify key on the provider's website

### "Rate limit exceeded"

- Wait 1 hour for limits to reset
- Consider spacing out API requests
- Both services have generous free limits

---

## 📊 Testing API Keys

### Test Pexels API:

```powershell
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('PEXELS_API_KEY')
headers = {'Authorization': api_key}
response = requests.get('https://api.pexels.com/v1/search?query=nature&per_page=1', headers=headers)

if response.status_code == 200:
    print('✅ Pexels API: Working!')
else:
    print(f'❌ Pexels API Error: {response.status_code}')
"
```

### Test Pixabay API:

```powershell
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('PIXABAY_API_KEY')
response = requests.get(f'https://pixabay.com/api/?key={api_key}&q=nature&per_page=3')

if response.status_code == 200:
    print('✅ Pixabay API: Working!')
else:
    print(f'❌ Pixabay API Error: {response.status_code}')
"
```

---

## 📋 Checklist

Before proceeding to next step:

- [ ] Pexels account created
- [ ] Pexels API key obtained
- [ ] Pexels API key added to `.env`
- [ ] Pixabay account created
- [ ] Pixabay API key obtained
- [ ] Pixabay API key added to `.env`
- [ ] `.env` file saved
- [ ] Configuration test passed

---

## ⏭️ Next Steps

After adding both API keys:

1. ✅ Save `.env` file
2. ✅ Run verification test (see above)
3. ✅ Verify `.env` is in `.gitignore`
4. ⏭️ **Proceed to Prompt #5**: YouTube OAuth (optional)
5. ⏭️ **Proceed to Prompt #6**: Final system verification

---

## 💡 Why These APIs?

### Pexels:

- High-quality HD/4K videos
- No attribution required
- Clean, professional content
- Great for nature, tech, lifestyle content

### Pixabay:

- Huge library (2.7M+ assets)
- Images AND videos
- Multiple languages supported
- Excellent for diverse content needs

### Combined Benefits:

- **Redundancy**: If one API is down, use the other
- **Variety**: Access to different content libraries
- **Reliability**: Fallback options for content sourcing
- **FREE**: No costs for high-quality content

---

**Time to Complete**: 10-15 minutes  
**Cost**: $0 (100% FREE)  
**Difficulty**: ⚡ Easy

---

_Prompt #4 of 6 | Status: API Keys Configuration_
