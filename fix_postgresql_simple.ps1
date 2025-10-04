# PostgreSQL Password Reset - Simple Method
# Run this script as Administrator

Write-Host "`nPostgreSQL Password Reset - Simple Method" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$newPassword = "FacelessYT2025!"

# Method 1: Try setting password with current unknown password
Write-Host "Attempting to reset password..." -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: When prompted for password, try these in order:" -ForegroundColor Cyan
Write-Host "  1. Press ENTER (empty password)" -ForegroundColor White
Write-Host "  2. Type: postgres" -ForegroundColor White
Write-Host "  3. Type: admin" -ForegroundColor White
Write-Host "  4. Type: root" -ForegroundColor White
Write-Host ""
Write-Host "Connecting to PostgreSQL..." -ForegroundColor Yellow

# Try with psql and let user type password interactively
& 'C:\Program Files\PostgreSQL\14\bin\psql.exe' -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD '$newPassword';"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Password changed to: $newPassword" -ForegroundColor Green
    Write-Host ""
    
    # Test the new password
    Write-Host "Testing new password..." -ForegroundColor Yellow
    $env:PGPASSWORD = $newPassword
    $testResult = & 'C:\Program Files\PostgreSQL\14\bin\psql.exe' -U postgres -c "SELECT version();" 2>&1
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] New password works!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Testing database connection with Python..." -ForegroundColor Yellow
        python test_databases.py
    }
    else {
        Write-Host "[WARNING] Could not verify new password" -ForegroundColor Yellow
    }
}
else {
    Write-Host "`n[FAILED] Could not connect to PostgreSQL" -ForegroundColor Red
    Write-Host ""
    Write-Host "If you don't know the current password, try:" -ForegroundColor Yellow
    Write-Host "  1. Uninstall PostgreSQL: choco uninstall postgresql14 -y" -ForegroundColor White
    Write-Host "  2. Reinstall with known password: choco install postgresql14 --params `"/Password:$newPassword`" -y" -ForegroundColor White
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
