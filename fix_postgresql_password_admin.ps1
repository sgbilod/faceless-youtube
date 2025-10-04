# PostgreSQL Password Fix Script
# Run this script as Administrator

Write-Host "`nPostgreSQL Password Reset Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

$configPath = "C:\Program Files\PostgreSQL\14\data\pg_hba.conf"
$backupPath = "$configPath.backup"

# Step 1: Backup current config
Write-Host "Step 1: Creating backup..." -ForegroundColor Yellow
Copy-Item $configPath $backupPath -Force
Write-Host "   [OK] Backup created: pg_hba.conf.backup`n" -ForegroundColor Green

# Step 2: Change authentication to trust
Write-Host "Step 2: Changing authentication to trust mode..." -ForegroundColor Yellow
(Get-Content $configPath) -replace 'scram-sha-256', 'trust' | Set-Content $configPath
Write-Host "   [OK] Authentication changed to trust`n" -ForegroundColor Green

# Step 3: Restart PostgreSQL service
Write-Host "Step 3: Restarting PostgreSQL service..." -ForegroundColor Yellow
Restart-Service postgresql-x64-14
Start-Sleep -Seconds 3
Write-Host "   [OK] Service restarted`n" -ForegroundColor Green

# Step 4: Set new password
Write-Host "Step 4: Setting password to 'FacelessYT2025!'..." -ForegroundColor Yellow
& 'C:\Program Files\PostgreSQL\14\bin\psql.exe' -U postgres -c "ALTER USER postgres WITH PASSWORD 'FacelessYT2025!';"
Write-Host "   [OK] Password updated`n" -ForegroundColor Green

# Step 5: Restore original authentication
Write-Host "Step 5: Restoring scram-sha-256 authentication..." -ForegroundColor Yellow
Copy-Item $backupPath $configPath -Force
Write-Host "   [OK] Authentication restored`n" -ForegroundColor Green

# Step 6: Restart PostgreSQL again
Write-Host "Step 6: Restarting PostgreSQL with new settings..." -ForegroundColor Yellow
Restart-Service postgresql-x64-14
Start-Sleep -Seconds 3
Write-Host "   [OK] Service restarted`n" -ForegroundColor Green

# Step 7: Test connection
Write-Host "Step 7: Testing connection..." -ForegroundColor Yellow
Write-Host ""
python test_databases.py

Write-Host "`n=================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] PostgreSQL Password Fix Complete!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Password: FacelessYT2025!" -ForegroundColor Cyan
Write-Host ""
