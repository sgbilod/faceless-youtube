# 🔐 PostgreSQL Password Fix - Prompt #3

## Problem

PostgreSQL is installed and running, but the password doesn't match `.env` file configuration.

**Current State:**

- ✅ PostgreSQL service: Running
- ✅ MongoDB: Connected
- ✅ Redis: Connected
- ❌ PostgreSQL: Password authentication failed

**Required Password:** `FacelessYT2025!` (from `.env` file)

---

## 🚀 Quick Fix (5 minutes)

### Option 1: Reset Password via Windows Search

1. **Open SQL Shell (psql)**:

   - Press `Windows Key`
   - Type: `sql shell`
   - Click: **SQL Shell (psql)**

2. **Press Enter 4 times** to accept defaults:

   ```
   Server [localhost]: [Press Enter]
   Database [postgres]: [Press Enter]
   Port [5432]: [Press Enter]
   Username [postgres]: [Press Enter]
   Password for user postgres: [Type current password or press Enter]
   ```

3. **If password fails**, close and try **Option 2**.

4. **If connected**, run this command:

   ```sql
   ALTER USER postgres WITH PASSWORD 'FacelessYT2025!';
   ```

5. **Exit**:
   ```sql
   \q
   ```

---

### Option 2: Edit Authentication File (No Password Needed)

1. **Open File Explorer**: `Windows Key + E`

2. **Navigate to**:

   ```
   C:\Program Files\PostgreSQL\14\data\pg_hba.conf
   ```

3. **Open with Notepad** (right-click → Open with → Notepad)

4. **Find these lines** (near bottom):

   ```
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            scram-sha-256
   # IPv6 local connections:
   host    all             all             ::1/128                 scram-sha-256
   ```

5. **Change `scram-sha-256` to `trust`**:

   ```
   # IPv4 local connections:
   host    all             all             127.0.0.1/32            trust
   # IPv6 local connections:
   host    all             all             ::1/128                 trust
   ```

6. **Save and close** (you may need to run Notepad as Administrator)

7. **Restart PostgreSQL**:

   ```powershell
   Restart-Service postgresql-x64-14
   ```

8. **Now set the password** (no password required):

   ```powershell
   & 'C:\Program Files\PostgreSQL\14\bin\psql.exe' -U postgres -c "ALTER USER postgres WITH PASSWORD 'FacelessYT2025!';"
   ```

9. **Revert authentication back** (change `trust` back to `scram-sha-256`):

   - Edit `pg_hba.conf` again
   - Change `trust` → `scram-sha-256`
   - Save

10. **Restart PostgreSQL again**:
    ```powershell
    Restart-Service postgresql-x64-14
    ```

---

### Option 3: Reinstall PostgreSQL (Last Resort)

If both options fail:

```powershell
# Uninstall
choco uninstall postgresql14 -y

# Reinstall with password
choco install postgresql14 --params "/Password:FacelessYT2025!" -y
```

---

## ✅ Verification

After fixing password, test connection:

```powershell
python test_databases.py
```

**Expected Output:**

```
✅ PostgreSQL: Connected
📌 Version: 14.x
✅ MongoDB: Connected
📌 Version: 8.2.1
✅ Redis: Connected
```

---

## 🎯 Impact on System Health

**Current:** 50% (3/6 components healthy)

**After fix:** 67% (4/6 components healthy)

- ✅ Configuration: HEALTHY
- ✅ Python Dependencies: HEALTHY (after Prompt #1 fix)
- ✅ File System: HEALTHY
- ✅ Database Connections: HEALTHY (after PostgreSQL password fix) ← **IMPROVEMENT**
- ✅ External APIs: HEALTHY
- ⚠️ Application Services: Needs investigation (scheduler import issue)

---

## 📞 Troubleshooting

### "Access Denied" when editing pg_hba.conf

- Right-click Notepad
- Select "Run as administrator"
- Then open the file

### "Service not found" when restarting

```powershell
# Check service name
Get-Service -Name "*postgresql*"

# Use exact name
Restart-Service <exact-service-name>
```

### Still can't connect after password reset

```powershell
# Check PostgreSQL logs
Get-Content "C:\Program Files\PostgreSQL\14\data\log\postgresql-*.log" -Tail 50
```

---

## 🚀 Next Steps After Fix

1. ✅ **Verify all databases**: `python test_databases.py`
2. ⏭️ **Proceed to Prompt #4**: Configure API keys (Pexels, Pixabay)
3. ⏭️ **Proceed to Prompt #5**: Setup YouTube OAuth (optional)
4. ⏭️ **Proceed to Prompt #6**: Final system verification
5. 🎯 **Target**: 80-100% system health

---

**Status:** PostgreSQL is installed and running - just needs password configuration.

**Recommendation:** Use **Option 2** (edit pg_hba.conf) - most reliable and doesn't require knowing current password.
