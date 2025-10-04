# PostgreSQL Password Guesser
# Try common default passwords

$passwords = @("", "postgres", "admin", "root", "password", "123456", "pgadmin")
$newPassword = "FacelessYT2025!"

Write-Host "`nTrying common PostgreSQL passwords..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

foreach ($pwd in $passwords) {
    $displayPwd = if ($pwd -eq "") { "(empty)" } else { $pwd }
    Write-Host "Trying password: $displayPwd..." -ForegroundColor Yellow -NoNewline
    
    $env:PGPASSWORD = $pwd
    $result = & 'C:\Program Files\PostgreSQL\14\bin\psql.exe' -U postgres -c "SELECT 1;" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " SUCCESS!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Found working password: $displayPwd" -ForegroundColor Green
        Write-Host "Now changing to: $newPassword" -ForegroundColor Yellow
        Write-Host ""
        
        $changeResult = & 'C:\Program Files\PostgreSQL\14\bin\psql.exe' -U postgres -c "ALTER USER postgres WITH PASSWORD '$newPassword';"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Password changed to: $newPassword" -ForegroundColor Green
            Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
            
            Write-Host ""
            Write-Host "Testing new password..." -ForegroundColor Yellow
            python test_databases.py
            exit 0
        }
        else {
            Write-Host "[FAILED] Could not change password" -ForegroundColor Red
            Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
            exit 1
        }
    }
    else {
        Write-Host " Failed" -ForegroundColor Red
    }
}

Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "[FAILED] None of the common passwords worked" -ForegroundColor Red
Write-Host ""
Write-Host "Options:" -ForegroundColor Yellow
Write-Host "  1. Reinstall PostgreSQL:" -ForegroundColor White
Write-Host "     choco uninstall postgresql14 -y" -ForegroundColor Cyan
Write-Host "     choco install postgresql14 --params `"/Password:$newPassword`" -y" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Or continue without PostgreSQL (MongoDB + Redis work fine)" -ForegroundColor White
Write-Host ""
