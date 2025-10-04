# 🗄️ PROMPT #3: Database Setup Guide

**Status:** ⚠️ Requires Administrator Privileges  
**Date:** October 4, 2025

---

## 🚨 Important Notice

Database installation requires **Administrator privileges** which the current PowerShell session does not have.

---

## ✅ **OPTION 1: Quick Install with Chocolatey (Recommended)**

### Step 1: Open PowerShell as Administrator

1. Press `Win + X`
2. Select "**Windows PowerShell (Admin)**" or "**Terminal (Admin)**"
3. Click "Yes" on UAC prompt

### Step 2: Navigate to Project

```powershell
cd C:\FacelessYouTube
```

### Step 3: Install PostgreSQL

```powershell
choco install postgresql14 --params "/Password:FacelessYT2025!" -y
```

**Installation time:** 3-5 minutes

**What it does:**
- Installs PostgreSQL 14
- Creates Windows Service (auto-starts)
- Sets postgres user password to: `FacelessYT2025!`
- Adds PostgreSQL to PATH

### Step 4: Install MongoDB

```powershell
choco install mongodb -y
```

**Installation time:** 2-4 minutes

**What it does:**
- Installs MongoDB Community 6.0+
- Creates Windows Service (auto-starts)
- Configures default data directory
- Adds MongoDB to PATH

### Step 5: Verify Services are Running

```powershell
Get-Service -Name "*postgresql*", "*mongo*" | Select-Object Name, Status, DisplayName
```

**Expected output:**
```
Name                Status  DisplayName
----                ------  -----------
postgresql-x64-14   Running PostgreSQL Database Server 14
MongoDB             Running MongoDB
```

### Step 6: Configure .env File

Edit `C:\FacelessYouTube\.env` and add:

```env
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=faceless_youtube
DB_USER=postgres
DB_PASSWORD=FacelessYT2025!

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=faceless_youtube_assets

# Redis (optional - already working)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Step 7: Create PostgreSQL Database

```powershell
# Connect to PostgreSQL and create database
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -c "CREATE DATABASE faceless_youtube;"
```

When prompted, enter password: `FacelessYT2025!`

### Step 8: Test Connections

```powershell
# Test PostgreSQL
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:FacelessYT2025!@localhost:5432/postgres'); print('✅ PostgreSQL connected'); conn.close()"

# Test MongoDB
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); client.server_info(); print('✅ MongoDB connected')"
```

### Step 9: Run Diagnostics

```powershell
python scripts/diagnostics.py
```

**Expected improvement:**
```
Component: Database Connections - HEALTHY ✅
  ✅ PASSED (3):
    - PostgreSQL: Connected
    - MongoDB: Connected
    - Redis: Connected
```

---

## ✅ **OPTION 2: Manual Installation (If Chocolatey Fails)**

### PostgreSQL Manual Install

1. **Download Installer:**
   - Visit: https://www.postgresql.org/download/windows/
   - Download PostgreSQL 14+ Windows Installer

2. **Run Installer:**
   - Double-click the `.exe` file
   - Click "Next" through setup
   - **Important:** Remember the password you set for `postgres` user
   - Select port: `5432` (default)
   - Select locale: Default
   - Complete installation

3. **Verify Installation:**
   ```powershell
   Get-Service postgresql-x64-14
   ```

4. **Start Service (if not running):**
   ```powershell
   net start postgresql-x64-14
   ```

### MongoDB Manual Install

1. **Download Installer:**
   - Visit: https://www.mongodb.com/try/download/community
   - Select: Windows, MSI package
   - Download MongoDB Community Server 6.0+

2. **Run Installer:**
   - Double-click the `.msi` file
   - Choose "Complete" installation
   - Install MongoDB as a Service: ✅ **Yes**
   - Service Name: `MongoDB`
   - Data Directory: `C:\Program Files\MongoDB\Server\6.0\data`
   - Log Directory: `C:\Program Files\MongoDB\Server\6.0\log`

3. **Verify Installation:**
   ```powershell
   Get-Service MongoDB
   ```

4. **Start Service (if not running):**
   ```powershell
   net start MongoDB
   ```

---

## 🛠️ Troubleshooting

### Issue: PostgreSQL service won't start

**Check Event Viewer:**
```powershell
Get-EventLog -LogName Application -Source PostgreSQL -Newest 10
```

**Common fixes:**
1. Port 5432 already in use - change port in `postgresql.conf`
2. Data directory permissions issue - check folder permissions
3. Service user account issue - reconfigure service

### Issue: MongoDB service won't start

**Check MongoDB logs:**
```powershell
Get-Content "C:\Program Files\MongoDB\Server\6.0\log\mongod.log" -Tail 50
```

**Common fixes:**
1. Port 27017 already in use - change port in `mongod.cfg`
2. Lock file exists - delete `C:\Program Files\MongoDB\Server\6.0\data\mongod.lock`
3. Insufficient permissions - run as administrator

### Issue: Can't connect from Python

**Check firewall:**
```powershell
# Allow PostgreSQL
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432

# Allow MongoDB
netsh advfirewall firewall add rule name="MongoDB" dir=in action=allow protocol=TCP localport=27017
```

**Verify services are listening:**
```powershell
netstat -an | Select-String "5432|27017"
```

---

## 📊 Verification Checklist

After installation, verify:

- [ ] PostgreSQL service is **Running**
- [ ] MongoDB service is **Running**
- [ ] `.env` file has database credentials
- [ ] PostgreSQL database `faceless_youtube` created
- [ ] Python can connect to PostgreSQL
- [ ] Python can connect to MongoDB
- [ ] Diagnostics show 3/3 database connections pass

---

## 🎯 Quick Verification Script

Save this as `test_databases.py` and run it:

```python
#!/usr/bin/env python
"""Test database connections."""

import sys
from colorama import init, Fore, Style

init(autoreset=True)

print(f"\n{Fore.CYAN}🔍 Testing Database Connections{Style.RESET_ALL}")
print("=" * 50)

# Test PostgreSQL
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='postgres',
        user='postgres',
        password='FacelessYT2025!'
    )
    conn.close()
    print(f"{Fore.GREEN}✅ PostgreSQL: Connected{Style.RESET_ALL}")
    postgres_ok = True
except Exception as e:
    print(f"{Fore.RED}❌ PostgreSQL: {e}{Style.RESET_ALL}")
    postgres_ok = False

# Test MongoDB
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    info = client.server_info()
    print(f"{Fore.GREEN}✅ MongoDB: Version {info['version']}{Style.RESET_ALL}")
    mongodb_ok = True
except Exception as e:
    print(f"{Fore.RED}❌ MongoDB: {e}{Style.RESET_ALL}")
    mongodb_ok = False

# Test Redis (should already work)
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
    r.ping()
    print(f"{Fore.GREEN}✅ Redis: Connected{Style.RESET_ALL}")
    redis_ok = True
except Exception as e:
    print(f"{Fore.YELLOW}⚠️  Redis: {e} (optional){Style.RESET_ALL}")
    redis_ok = False

print("\n" + "=" * 50)

if postgres_ok and mongodb_ok:
    print(f"{Fore.GREEN}🎉 All databases operational!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}➡️  Ready for Prompt #4: Environment Configuration{Style.RESET_ALL}")
    sys.exit(0)
else:
    print(f"{Fore.YELLOW}⚠️  Some databases not available{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Review the errors above and troubleshoot{Style.RESET_ALL}")
    sys.exit(1)
```

Run it:
```powershell
python test_databases.py
```

---

## 🚀 After Successful Setup

1. **Update `.env` file** with database credentials
2. **Run diagnostics:** `python scripts/diagnostics.py`
3. **Commit changes:** 
   ```powershell
   git add .env
   git commit -m "config: add database credentials for PostgreSQL and MongoDB"
   ```
4. **Proceed to Prompt #4:** Environment Configuration

---

## 📚 Reference Links

- PostgreSQL Download: https://www.postgresql.org/download/windows/
- MongoDB Download: https://www.mongodb.com/try/download/community
- PostgreSQL Documentation: https://www.postgresql.org/docs/14/
- MongoDB Documentation: https://www.mongodb.com/docs/manual/

---

## ⏱️ Estimated Time

- **Option 1 (Chocolatey):** 10-15 minutes
- **Option 2 (Manual):** 20-30 minutes

---

**Created:** October 4, 2025  
**For:** Faceless YouTube Automation Platform v2.0  
**Prompt:** #3 of 6
