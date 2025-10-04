# 🔍 PIP INSTALLATION MONITOR
# Auto-refreshing progress tracker for pip install

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  📦 PYTHON PACKAGE INSTALLATION MONITOR" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Log File: " -NoNewline -ForegroundColor Yellow
Write-Host "pip_install_v2.log" -ForegroundColor White
Write-Host "  Started: " -NoNewline -ForegroundColor Yellow
Write-Host (Get-Date -Format "HH:mm:ss") -ForegroundColor White
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$logFile = "pip_install_v2.log"
$lastSize = 0
$checkInterval = 5  # seconds
$noChangeCount = 0
$maxNoChange = 6  # 30 seconds of no activity = likely complete

while ($true) {
    if (Test-Path $logFile) {
        $currentSize = (Get-Item $logFile).Length
        
        if ($currentSize -ne $lastSize) {
            # New content added
            $noChangeCount = 0
            
            # Read and display last 20 lines
            Clear-Host
            Write-Host "`n" -NoNewline
            Write-Host "=" * 80 -ForegroundColor Cyan
            Write-Host "  📦 PYTHON PACKAGE INSTALLATION MONITOR" -ForegroundColor Cyan
            Write-Host "=" * 80 -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  Log File: " -NoNewline -ForegroundColor Yellow
            Write-Host "pip_install_v2.log" -ForegroundColor White
            Write-Host "  Size: " -NoNewline -ForegroundColor Yellow
            Write-Host "$([math]::Round($currentSize/1KB, 2)) KB" -ForegroundColor White
            Write-Host "  Last Update: " -NoNewline -ForegroundColor Yellow
            Write-Host (Get-Date -Format "HH:mm:ss") -ForegroundColor White
            Write-Host ""
            Write-Host "=" * 80 -ForegroundColor Cyan
            Write-Host ""
            
            # Get last 20 lines
            $lines = Get-Content $logFile -Tail 20
            
            foreach ($line in $lines) {
                # Color code based on content
                if ($line -match "Successfully installed|Successfully built") {
                    Write-Host "✅ $line" -ForegroundColor Green
                }
                elseif ($line -match "ERROR|error:|Error:|failed|Failed") {
                    Write-Host "❌ $line" -ForegroundColor Red
                }
                elseif ($line -match "Downloading|Collecting|Using cached") {
                    Write-Host "📥 $line" -ForegroundColor Cyan
                }
                elseif ($line -match "Installing|Building|Preparing") {
                    Write-Host "🔨 $line" -ForegroundColor Yellow
                }
                elseif ($line -match "Requirement already satisfied") {
                    Write-Host "✓ $line" -ForegroundColor DarkGray
                }
                else {
                    Write-Host "  $line" -ForegroundColor White
                }
            }
            
            Write-Host ""
            Write-Host "=" * 80 -ForegroundColor Cyan
            Write-Host "  🔄 Monitoring... (Ctrl+C to exit)" -ForegroundColor Yellow
            Write-Host "=" * 80 -ForegroundColor Cyan
            
            $lastSize = $currentSize
        }
        else {
            # No new content
            $noChangeCount++
            
            if ($noChangeCount -ge $maxNoChange) {
                # Check if installation completed
                $lastLines = Get-Content $logFile -Tail 5 | Out-String
                
                if ($lastLines -match "Successfully installed") {
                    Clear-Host
                    Write-Host "`n" -NoNewline
                    Write-Host "=" * 80 -ForegroundColor Green
                    Write-Host "  ✅ INSTALLATION COMPLETE!" -ForegroundColor Green
                    Write-Host "=" * 80 -ForegroundColor Green
                    Write-Host ""
                    
                    # Extract package count
                    if ($lastLines -match "Successfully installed (.+)") {
                        $packages = $matches[1] -split " " | Where-Object { $_ -match "-" }
                        Write-Host "  📦 Installed Packages: " -NoNewline -ForegroundColor Yellow
                        Write-Host "$($packages.Count)" -ForegroundColor Green
                    }
                    
                    Write-Host "  ⏱️  Completed: " -NoNewline -ForegroundColor Yellow
                    Write-Host (Get-Date -Format "HH:mm:ss") -ForegroundColor White
                    Write-Host ""
                    Write-Host "=" * 80 -ForegroundColor Green
                    Write-Host ""
                    Write-Host "  🎯 NEXT STEPS:" -ForegroundColor Cyan
                    Write-Host ""
                    Write-Host "  1. Verify installation:" -ForegroundColor White
                    Write-Host "     python scripts/diagnostics.py" -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "  2. Test critical imports:" -ForegroundColor White
                    Write-Host "     python -c `"import torch; print('✅ PyTorch', torch.__version__)`"" -ForegroundColor Gray
                    Write-Host "     python -c `"import pydantic; print('✅ Pydantic', pydantic.__version__)`"" -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "  3. Commit changes:" -ForegroundColor White
                    Write-Host "     git add requirements.txt pip_install_v2.log" -ForegroundColor Gray
                    Write-Host "     git commit -m `"fix(deps): Python 3.13 compatibility complete`"" -ForegroundColor Gray
                    Write-Host "     git push" -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "=" * 80 -ForegroundColor Green
                    Write-Host ""
                    
                    # Play success sound (if available)
                    [Console]::Beep(800, 200)
                    Start-Sleep -Milliseconds 100
                    [Console]::Beep(1000, 200)
                    Start-Sleep -Milliseconds 100
                    [Console]::Beep(1200, 300)
                    
                    break
                }
                elseif ($lastLines -match "ERROR|error:|failed") {
                    Clear-Host
                    Write-Host "`n" -NoNewline
                    Write-Host "=" * 80 -ForegroundColor Red
                    Write-Host "  ❌ INSTALLATION FAILED!" -ForegroundColor Red
                    Write-Host "=" * 80 -ForegroundColor Red
                    Write-Host ""
                    Write-Host "  Check log file for details:" -ForegroundColor Yellow
                    Write-Host "  Get-Content pip_install_v2.log -Tail 50" -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "=" * 80 -ForegroundColor Red
                    Write-Host ""
                    
                    # Play error sound
                    [Console]::Beep(400, 500)
                    
                    break
                }
            }
            
            # Show waiting indicator
            Write-Host "`r  ⏳ Waiting for updates... ($($noChangeCount * $checkInterval)s idle)" -NoNewline -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "`r  ⏳ Waiting for log file to appear..." -NoNewline -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds $checkInterval
}

Write-Host ""
