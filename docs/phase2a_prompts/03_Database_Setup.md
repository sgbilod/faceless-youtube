# 🗄️ PROMPT #3: Database Services Setup

## Phase 2A - Critical Issue Resolution

**Reference Code:** `[REF:PROMPT-003]`  
**Complexity:** ⚙️ Medium  
**Estimated Time:** 10-20 minutes  
**Prerequisites:** PROMPT #1, #2 complete

---

## 🎯 OBJECTIVE

Start and configure PostgreSQL, MongoDB, and Redis database services required for video metadata, asset storage, and caching.

**Services to Configure:**

- PostgreSQL (port 5432) - Relational data
- MongoDB (port 27017) - Asset storage
- Redis (port 6379) - Caching and job queues

---

## 📋 COPILOT PROMPT

````
GITHUB COPILOT DIRECTIVE: DATABASE SERVICES SETUP
[REF:PROMPT-003]

CONTEXT:
- Project: Faceless YouTube Automation Platform v2.0
- Phase: 2A - Critical Issue Resolution
- Task: Start and configure 3 database services
- Databases: PostgreSQL, MongoDB, Redis

CURRENT STATE:
Diagnostic report shows:
❌ PostgreSQL: Connection failed - "no password supplied"
❌ MongoDB: Connection refused - Service not running
✅ Redis: Connection successful

Impact: Cannot store video metadata, asset information, or manage job queues

TASK:
1. Check which database services are installed
2. Start PostgreSQL service
3. Start MongoDB service
4. Verify Redis is running
5. Test all three connections
6. Update .env with database credentials

SPECIFIC ACTIONS FOR WINDOWS:

Step 1: Check Installed Services
Execute in PowerShell (as Administrator):
```powershell
# Check PostgreSQL
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Check MongoDB
Get-Service | Where-Object {$_.Name -like "*mongo*"}

# Check Redis
Get-Service | Where-Object {$_.Name -like "*redis*"}
````

Step 2: Start PostgreSQL
Execute in PowerShell (as Administrator):

```powershell
# Find the exact service name
$pgService = Get-Service | Where-Object {$_.Name -like "*postgresql*"} | Select-Object -First 1

# Start service
Start-Service $pgService.Name

# Verify
Get-Service $pgService.Name
```

Expected status: Running

Step 3: Start MongoDB
Execute in PowerShell (as Administrator):

```powershell
# Start MongoDB
Start-Service MongoDB

# Verify
Get-Service MongoDB
```

Expected status: Running

Step 4: Verify Redis
Execute in PowerShell:

```powershell
Get-Service | Where-Object {$_.Name -like "*redis*"}
```

If not running:

```powershell
Start-Service Redis
```

Step 5: Test Connections
Execute in terminal (regular PowerShell):

```powershell
# Test PostgreSQL
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:password@localhost:5432/postgres'); print('✅ PostgreSQL OK')"

# Test MongoDB
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('✅ MongoDB OK')"

# Test Redis
python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('✅ Redis OK')"
```

Step 6: Update .env File
Set database credentials in .env:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=faceless_youtube
DB_USER=postgres
DB_PASSWORD=your_secure_password

MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB=faceless_youtube

REDIS_HOST=localhost
REDIS_PORT=6379
```

Step 7: Run Diagnostics

```powershell
python scripts/diagnostics.py
```

Check Database Connections component shows all 3 passing

REQUIREMENTS:

- Windows with Administrator access
- PostgreSQL, MongoDB, Redis installed
- Python packages: psycopg2, pymongo, redis (installed in PROMPT #1)

IF SERVICES NOT INSTALLED:

For PostgreSQL:

1. Download from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for postgres user

For MongoDB:

1. Download from https://www.mongodb.com/try/download/community
2. Install as Windows Service
3. Use default port 27017

For Redis:

1. Download from https://github.com/microsoftarchive/redis/releases
2. Or use: `choco install redis-64` (if Chocolatey installed)
3. Install as Windows Service

ERROR HANDLING:

- If service won't start, check Windows Event Viewer for errors
- If port already in use, check for conflicts with other services
- If connection fails, verify firewall settings allow localhost connections
- If PostgreSQL password fails, may need to reset via pgAdmin

DELIVERABLES:

1. All 3 database services running
2. All 3 connection tests passing
3. .env updated with correct credentials
4. Diagnostic report showing Database Connections: HEALTHY

SUCCESS CRITERIA:
✅ PostgreSQL service running and connectable
✅ MongoDB service running and connectable
✅ Redis service running and connectable
✅ Diagnostic test shows 3/3 database connections pass
✅ .env file has correct database credentials

NEXT STEP:
Once complete, proceed to PROMPT #4 (Environment Configuration)

````

---

## 🔍 DETAILED INSTRUCTIONS

### For Windows Users

#### Start Services via GUI

1. **Open Services Manager:**
   - Press `Win+R`
   - Type: `services.msc`
   - Press Enter

2. **Find and Start Each Service:**
   - Scroll to find: `postgresql-x64-XX`, `MongoDB`, `Redis`
   - Right-click → Start
   - Set Startup Type → Automatic (for auto-start on boot)

#### Start Services via PowerShell

```powershell
# Run PowerShell as Administrator
# Start all services
Start-Service -Name "postgresql-x64-*"
Start-Service -Name "MongoDB"
Start-Service -Name "Redis"

# Verify all running
Get-Service -Name "postgresql-x64-*", "MongoDB", "Redis"
````

### For Linux/Mac Users

```bash
# PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot

# MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Redis
sudo systemctl start redis
sudo systemctl enable redis

# Verify all running
systemctl status postgresql mongod redis
```

Or with Homebrew (Mac):

```bash
brew services start postgresql
brew services start mongodb-community
brew services start redis
```

---

## ⚠️ TROUBLESHOOTING

### Issue: Services not found

**Check if installed:**

```powershell
# Windows
Get-Service | Select-String "postgres|mongo|redis"

# If empty, services not installed
```

**Solution:** Install missing services (see installation links above)

### Issue: PostgreSQL password authentication failed

**Reset PostgreSQL password:**

1. Open `pgAdmin 4`
2. Connect to server
3. Right-click `postgres` user → Properties
4. Set new password
5. Update `.env` file with new password

### Issue: MongoDB won't start

**Check logs:**

```powershell
# Windows
Get-Content "C:\Program Files\MongoDB\Server\*\log\mongod.log" -Tail 50
```

**Common fixes:**

- Delete `mongod.lock` file if exists
- Check data directory has write permissions
- Ensure port 27017 not in use

### Issue: Redis not installed on Windows

**Quick install with Chocolatey:**

```powershell
# Install Chocolatey first (if not installed)
# Then:
choco install redis-64

# Or download from:
# https://github.com/microsoftarchive/redis/releases
```

### Issue: Port already in use

**Check what's using the port:**

```powershell
# Check port 5432 (PostgreSQL)
netstat -ano | findstr :5432

# Check port 27017 (MongoDB)
netstat -ano | findstr :27017

# Check port 6379 (Redis)
netstat -ano | findstr :6379
```

**Solution:** Stop conflicting process or change database port in `.env`

---

## ✅ SUCCESS VERIFICATION

### Checklist

- [ ] PostgreSQL service is running
- [ ] MongoDB service is running
- [ ] Redis service is running
- [ ] All 3 connection tests pass
- [ ] `.env` file updated with credentials
- [ ] Diagnostic shows Database Connections: HEALTHY

### Comprehensive Test

```powershell
# Run all connection tests
python -c "
import psycopg2
from pymongo import MongoClient
import redis

try:
    # PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='postgres'
    )
    conn.close()
    print('✅ PostgreSQL: Connected')

    # MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    client.server_info()
    print('✅ MongoDB: Connected')

    # Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis: Connected')

    print('\n🎉 ALL DATABASES CONNECTED SUCCESSFULLY')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

**Expected Output:**

```
✅ PostgreSQL: Connected
✅ MongoDB: Connected
✅ Redis: Connected

🎉 ALL DATABASES CONNECTED SUCCESSFULLY
```

---

## 📊 BEFORE & AFTER

### Before

```
Component: Database Connections - UNHEALTHY ❌
  ✅ PASSED (1): Redis connection
  ❌ FAILED (2):
    - PostgreSQL: no password supplied
    - MongoDB: connection refused (not running)

Status: Data storage BLOCKED
```

### After

```
Component: Database Connections - HEALTHY ✅
  ✅ PASSED (3):
    - PostgreSQL: Connected
    - MongoDB: Connected
    - Redis: Connected

Status: All database services READY
```

---

## 🎯 NEXT STEPS

Once all database services are running:

1. **Test the setup:**

   ```powershell
   python scripts/diagnostics.py
   ```

2. **Proceed to PROMPT #4:** [Environment Configuration](04_Environment_Config.md)

3. **Mark this task complete** in your checklist

**Status Update:**

- ✅ Critical Issue #1: RESOLVED
- ✅ Critical Issue #2: RESOLVED
- ✅ Critical Issue #3: RESOLVED (PostgreSQL)
- ✅ Critical Issue #4: RESOLVED (MongoDB)
- ⏳ Critical Issue #5: Next
- ⏳ Critical Issue #6: Pending

---

## 💾 DATABASE SETUP TIPS

**Auto-start on Boot:**
Set services to start automatically:

```powershell
# Windows
Set-Service -Name "postgresql-x64-*" -StartupType Automatic
Set-Service -Name "MongoDB" -StartupType Automatic
Set-Service -Name "Redis" -StartupType Automatic
```

**Create Application Database:**

```sql
-- PostgreSQL
CREATE DATABASE faceless_youtube;

-- MongoDB
use faceless_youtube
db.createCollection("videos")
```

**Backup Configuration:**
Document your database passwords in a secure password manager!

---

_Reference: ISSUES_FOUND.md (Issues #4, #5), diagnostic_report.txt_  
_Generated: October 4, 2025_
