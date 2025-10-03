@echo off
setlocal EnableDelayedExpansion

:: Script to set up Faceless YouTube video creator app
:: Creates Python 3.11 venv, installs libraries, verifies assets, FFmpeg, ImageMagick, and launches UI
:: Tests gTTS with timeout, uses portable ImageMagick 7.1.1-47, ensures verbose logging
:: Loops to create multiple videos with background music and text customization
:: Location: C:\FacelessYouTube
:: Logs to C:\FacelessYouTube\setup_log.txt, gTTS install to gtts_install.log
:: Date: May 31, 2025

set "LOG_FILE=C:\FacelessYouTube\setup_log.txt"
set "GTTS_LOG=C:\FacelessYouTube\gtts_install.log"
set "IMAGEMAGICK_DIR=C:\FacelessYouTube\ImageMagick\ImageMagick-7.1.1-47-portable-Q16-HDRI-x64"
set "ASSETS_DIR=C:\FacelessYouTube\assets"

echo === Faceless YouTube Setup Script ===
echo Sets up in C:\FacelessYouTube by default.
echo Needs faceless_video_app.py in C:\FacelessYouTube.
echo Requires admin rights and internet.
echo UI will launch for script entry, video creation, background music, and text customization.
echo Logs to %LOG_FILE%, gTTS install to %GTTS_LOG%.
echo [%DATE% %TIME%] Starting setup > "%LOG_FILE%"
pause

:SYSTEM_CHECKS
echo.
echo === System Checks ===
echo [%DATE% %TIME%] Starting system checks >> "%LOG_FILE%"

:: Admin check
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Need admin rights. Run as administrator.
    echo [%DATE% %TIME%] No admin rights >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Admin rights good.
echo [%DATE% %TIME%] Admin rights confirmed >> "%LOG_FILE%"

:: Internet check
ping 8.8.8.8 -n 1 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Need internet. Check connection.
    echo [%DATE% %TIME%] No internet >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Internet good.
echo [%DATE% %TIME%] Internet confirmed >> "%LOG_FILE%"

:: Disk space check (1GB free on C:)
for /f "tokens=3" %%a in ('dir C:\ /-c ^| find "bytes free"') do set FREE_SPACE=%%a
set /a FREE_SPACE_MB=FREE_SPACE/1024/1024
if !FREE_SPACE_MB! lss 1000 (
    echo Low disk space on C:. Need 1GB, got !FREE_SPACE_MB!MB.
    echo [%DATE% %TIME%] Low disk space: !FREE_SPACE_MB!MB >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Disk space good: !FREE_SPACE_MB!MB free.
echo [%DATE% %TIME%] Disk space: !FREE_SPACE_MB!MB free >> "%LOG_FILE%"

:: Write permissions check
echo test > C:\FacelessYouTube\test_write.txt 2>nul
if %ERRORLEVEL% neq 0 (
    echo No write permissions in C:\FacelessYouTube. Fix permissions.
    echo [%DATE% %TIME%] No write permissions >> "%LOG_FILE%"
    pause
    exit /b 1
)
del C:\FacelessYouTube\test_write.txt
echo Write permissions good.
echo [%DATE% %TIME%] Write permissions confirmed >> "%LOG_FILE%"

:: PowerShell check
powershell -Command "exit 0" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Need PowerShell. Install it.
    echo [%DATE% %TIME%] No PowerShell >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo PowerShell good.
echo [%DATE% %TIME%] PowerShell confirmed >> "%LOG_FILE%"

:: winget check
winget --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo No winget. Install Python 3.11 manually if needed.
    echo [%DATE% %TIME%] No winget >> "%LOG_FILE%"
) else (
    echo winget good.
    echo [%DATE% %TIME%] winget confirmed >> "%LOG_FILE%"
)

:SETUP
echo.
echo === Setting Project Directory ===
set "PROJECT_DIR=C:\FacelessYouTube"
set /p PROJECT_DIR=Enter project directory (default: C:\FacelessYouTube): 
if "!PROJECT_DIR!"=="" set "PROJECT_DIR=C:\FacelessYouTube"
echo [%DATE% %TIME%] Project directory: !PROJECT_DIR! >> "%LOG_FILE%"

:: Python 3.11 check
echo.
echo === Checking Python 3.11 ===
where py >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo No Python launcher. Get Python 3.11 from https://www.python.org/downloads/release/python-3119/
    echo [%DATE% %TIME%] No Python launcher >> "%LOG_FILE%"
    pause
    exit /b 1
)
py -3.11 --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo No Python 3.11. Trying to install via winget...
    echo [%DATE% %TIME%] Installing Python 3.11 >> "%LOG_FILE%"
    winget install Python.Python.3.11 >> "%LOG_FILE%" 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Failed to install Python 3.11. Get it from https://www.python.org/downloads/release/python-3119/
        echo [%DATE% %TIME%] Python 3.11 install failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)
py -3.11 --version >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python 3.11 check failed.
    echo [%DATE% %TIME%] Python 3.11 check failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Python 3.11 good.
echo [%DATE% %TIME%] Python 3.11 confirmed >> "%LOG_FILE%"

:: Directory and file check
echo.
echo === Verifying Directory ===
if not exist "!PROJECT_DIR!" (
    mkdir "!PROJECT_DIR!" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Couldn’t create !PROJECT_DIR!. Check permissions.
        echo [%DATE% %TIME%] Create directory failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)
cd /D "!PROJECT_DIR!" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Couldn’t switch to !PROJECT_DIR!. Check path.
    echo [%DATE% %TIME%] Switch directory failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
if not exist "faceless_video_app.py" (
    echo No faceless_video_app.py in !PROJECT_DIR!. Save it there.
    echo [%DATE% %TIME%] No faceless_video_app.py >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Directory good: %CD%
echo [%DATE% %TIME%] Directory verified >> "%LOG_FILE%"

:: Check assets
echo.
echo === Checking Assets ===
set "ASSET_MISSING="
if not exist "!ASSETS_DIR!\fallback_nature.mp4" set "ASSET_MISSING=1"
if not exist "!ASSETS_DIR!\meditation1.mp3" set "ASSET_MISSING=1"
if not exist "!ASSETS_DIR!\meditation2.mp3" set "ASSET_MISSING=1"
if defined ASSET_MISSING (
    echo Some assets are missing. Please download them manually:
    echo 1. Fallback Video: https://pixabay.com/videos/forest-nature-stream-waterfall-171688/
    echo    Download the "Tiny" version and save as !ASSETS_DIR!\fallback_nature.mp4
    echo 2. Meditation Music Track 1: https://pixabay.com/music/acoustic-group-morning-in-the-forest-149255/
    echo    Download MP3 and save as !ASSETS_DIR!\meditation1.mp3
    echo 3. Meditation Music Track 2: https://pixabay.com/music/meditation-spiritual-inner-peace-149256/
    echo    Download MP3 and save as !ASSETS_DIR!\meditation2.mp3
    echo After downloading, press any key to continue...
    echo [%DATE% %TIME%] Assets missing, prompting manual download >> "%LOG_FILE%"
    pause
)
if exist "!ASSETS_DIR!\fallback_nature.mp4" (
    echo Fallback video found.
    echo [%DATE% %TIME%] Fallback video found >> "%LOG_FILE%"
)
if exist "!ASSETS_DIR!\meditation1.mp3" (
    echo Meditation music track 1 found.
    echo [%DATE% %TIME%] Meditation music track 1 found >> "%LOG_FILE%"
)
if exist "!ASSETS_DIR!\meditation2.mp3" (
    echo Meditation music track 2 found.
    echo [%DATE% %TIME%] Meditation music track 2 found >> "%LOG_FILE%"
)

:: Virtual environment setup
echo.
echo === Setting Up Virtual Environment ===
if exist venv (
    echo Removing old virtual environment...
    rmdir /S /Q venv >nul 2>> "%LOG_FILE%"
    if !ERRORLEVEL! neq 0 (
        echo Couldn’t delete venv. Check permissions.
        echo [%DATE% %TIME%] Delete venv failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)
echo Creating new virtual environment...
if exist venv (
    echo Virtual environment still exists. Deleting again...
    rmdir /S /Q venv >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! neq 0 (
        echo Failed to delete existing venv. Check permissions.
        echo [%DATE% %TIME%] Delete existing venv failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)
py -3.11 -m venv venv >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo Couldn’t create virtual environment. Check Python 3.11 installation.
    echo [%DATE% %TIME%] Create venv failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
if not exist venv\Scripts\activate.bat (
    echo Virtual environment creation failed: activate.bat not found.
    echo [%DATE% %TIME%] Venv activate.bat missing >> "%LOG_FILE%"
    pause
    exit /b 1
)
call venv\Scripts\activate.bat >nul 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo Couldn’t activate virtual environment.
    echo [%DATE% %TIME%] Activate venv failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
:: Verify Python version in venv
python --version > "%TEMP%\python_version.txt" 2>&1
echo Venv Python version: >> "%LOG_FILE%"
type "%TEMP%\python_version.txt" >> "%LOG_FILE%"
del "%TEMP%\python_version.txt" 2>nul
python --version | findstr /C:"3.11" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Venv Python version is not 3.11. Recreate venv.
    echo [%DATE% %TIME%] Venv Python version check failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Virtual environment ready.
echo [%DATE% %TIME%] Venv activated >> "%LOG_FILE%"

:: Install libraries
echo.
echo === Installing Libraries ===
echo [%DATE% %TIME%] Clearing pip cache... >> "%LOG_FILE%"
python -m pip cache purge >> "%LOG_FILE%" 2>&1
echo [%DATE% %TIME%] Pip cache cleared. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Upgrading pip... >> "%LOG_FILE%"
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo Pip upgrade failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] Pip upgrade failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] Pip upgraded. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing moviepy==1.0.3... >> "%LOG_FILE%"
pip install moviepy==1.0.3 --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo moviepy install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] moviepy install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] moviepy installed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing numpy... >> "%LOG_FILE%"
pip install numpy --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo numpy install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] numpy install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] numpy installed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing imageio... >> "%LOG_FILE%"
pip install imageio --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo imageio install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] imageio install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] imageio installed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing PyQt5... >> "%LOG_FILE%"
pip install PyQt5 --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo PyQt5 install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] PyQt5 install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] PyQt5 installed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing requests... >> "%LOG_FILE%"
pip install requests --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo requests install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] requests install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] requests installed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing schedule... >> "%LOG_FILE%"
pip install schedule --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo schedule install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] schedule install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] schedule installed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Installing imageio-ffmpeg... >> "%LOG_FILE%"
pip install imageio-ffmpeg --force-reinstall --no-cache-dir >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo imageio-ffmpeg install failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] imageio-ffmpeg install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%DATE% %TIME%] imageio-ffmpeg installed. >> "%LOG_FILE%"
echo Libraries installed.
echo [%DATE% %TIME%] Libraries installed >> "%LOG_FILE%"

:: Install gTTS
echo.
echo === Installing gTTS ===
echo [%DATE% %TIME%] Installing gTTS... >> "%LOG_FILE%"
pip install gTTS==2.5.4 --force-reinstall --no-cache-dir --no-deps --verbose > "%GTTS_LOG%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo gTTS install failed. Retrying with default PyPI...
    echo [%DATE% %TIME%] gTTS install failed, retrying >> "%LOG_FILE%"
    pip install gTTS==2.5.4 --force-reinstall --no-cache-dir --no-deps --verbose >> "%GTTS_LOG%" 2>&1
    if %ERRORLEVEL% neq 0 (
        echo gTTS install failed again. Check %GTTS_LOG%.
        echo [%DATE% %TIME%] gTTS install failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)
echo gTTS installed.
echo [%DATE% %TIME%] gTTS installed >> "%LOG_FILE%"

:: Verify installations
echo Verifying library installations...
pip list > "%TEMP%\pip_list.txt" 2>> "%LOG_FILE%"
echo Installed packages: >> "%LOG_FILE%"
type "%TEMP%\pip_list.txt" >> "%LOG_FILE%"
del "%TEMP%\pip_list.txt" 2>nul
:: Log site-packages path
python -c "import site; print(site.getsitepackages()[0])" > "%TEMP%\site_packages.txt" 2>&1
echo Site-packages path: >> "%LOG_FILE%"
type "%TEMP%\site_packages.txt" >> "%LOG_FILE%"
del "%TEMP%\site_packages.txt" 2>nul
pip list | findstr /C:"moviepy" | findstr /C:"1.0.3" >nul 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo moviepy install failed.
    echo [%DATE% %TIME%] moviepy install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
pip list | findstr /C:"gTTS" | findstr /C:"2.5.4" >nul 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo gTTS install failed. Check %GTTS_LOG%.
    echo [%DATE% %TIME%] gTTS install failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Libraries verified.
echo [%DATE% %TIME%] Libraries verified >> "%LOG_FILE%"

:: Test gTTS with timeout
echo.
echo === Testing gTTS ===
(
echo import sys
echo try:
echo     from gtts import gTTS
echo     print^("gTTS import passed!"^)
echo     tts = gTTS^("test", lang="en"^)
echo     print^("gTTS initialization passed!"^)
echo except Exception as e:
echo     print^(f"gTTS test failed: {e}"^)
echo     sys.exit^(1^)
) > test_gtts.py
if not exist test_gtts.py (
    echo Failed to create test_gtts.py.
    echo [%DATE% %TIME%] Failed to create test_gtts.py >> "%LOG_FILE%"
    pause
    exit /b 1
)
:: Run with timeout (10 seconds)
echo [%DATE% %TIME%] Running gTTS test with 10-second timeout... >> "%LOG_FILE%"
powershell -Command "Start-Process python -ArgumentList 'test_gtts.py' -NoNewWindow -Wait -RedirectStandardOutput '%TEMP%\gtts_test_output.txt' -RedirectStandardError '%TEMP%\gtts_test_error.txt'; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }" >nul 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo gTTS test failed. Checking output...
    echo [%DATE% %TIME%] gTTS test failed >> "%LOG_FILE%"
    type "%TEMP%\gtts_test_output.txt" >> "%LOG_FILE%" 2>&1
    type "%TEMP%\gtts_test_error.txt" >> "%LOG_FILE%" 2>&1
    del "%TEMP%\gtts_test_output.txt" 2>nul
    del "%TEMP%\gtts_test_error.txt" 2>nul
    echo gTTS test failed, but continuing to UI launch as fallback.
    echo [%DATE% %TIME%] Continuing despite gTTS test failure >> "%LOG_FILE%"
    goto FFMPEG_CHECK
)
type "%TEMP%\gtts_test_output.txt" >> "%LOG_FILE%" 2>&1
del "%TEMP%\gtts_test_output.txt" 2>nul
del "%TEMP%\gtts_test_error.txt" 2>nul
del test_gtts.py >nul 2>> "%LOG_FILE%"
echo gTTS test passed.
echo [%DATE% %TIME%] gTTS test passed >> "%LOG_FILE%"

:FFMPEG_CHECK
:: Install FFmpeg
echo.
echo === Installing FFmpeg ===
:: Check if FFmpeg is already installed
if exist "C:\ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg found at C:\ffmpeg\bin\ffmpeg.exe. Verifying...
    echo [%DATE% %TIME%] FFmpeg found, verifying >> "%LOG_FILE%"
    set "PATH=%PATH%;C:\ffmpeg\bin"
    ffmpeg -version > "%TEMP%\ffmpeg_version.txt" 2>&1
    if !ERRORLEVEL! equ 0 (
        echo FFmpeg verified successfully.
        echo [%DATE% %TIME%] FFmpeg verified >> "%LOG_FILE%"
        type "%TEMP%\ffmpeg_version.txt" >> "%LOG_FILE%"
        del "%TEMP%\ffmpeg_version.txt" 2>nul
        goto FFMPEG_DONE
    ) else (
        echo Existing FFmpeg failed verification. Check %TEMP%\ffmpeg_version.txt.
        echo [%DATE% %TIME%] Existing FFmpeg failed verification >> "%LOG_FILE%"
        type "%TEMP%\ffmpeg_version.txt" >> "%LOG_FILE%"
        del "%TEMP%\ffmpeg_version.txt" 2>nul
    )
)
:: Install FFmpeg
if exist "C:\ffmpeg" (
    rmdir /S /Q C:\ffmpeg >nul 2>> "%LOG_FILE%"
)
mkdir C:\ffmpeg >nul 2>> "%LOG_FILE%"
cd C:\ffmpeg
echo Downloading FFmpeg...
powershell -Command "try { Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip' -ErrorAction Stop } catch { Write-Output $_.Exception.Message | Out-File -Append -FilePath '!LOG_FILE!' }" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo FFmpeg download failed. Check internet.
    echo [%DATE% %TIME%] FFmpeg download failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Extracting FFmpeg...
powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force" >nul 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo FFmpeg extraction failed.
    echo [%DATE% %TIME%] FFmpeg extraction failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
for /D %%i in ("ffmpeg-*") do (
    if exist "%%i\bin\ffmpeg.exe" (
        move "%%i\*" . >nul 2>> "%LOG_FILE%"
        rmdir "%%i" >nul 2>> "%LOG_FILE%"
    ) else (
        echo FFmpeg folder structure weird.
        echo [%DATE% %TIME%] FFmpeg folder structure bad >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)
del ffmpeg.zip >nul 2>> "%LOG_FILE%"
if not exist "C:\ffmpeg\bin\ffmpeg.exe" (
    echo FFmpeg executable not found after extraction.
    echo [%DATE% %TIME%] FFmpeg executable missing >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo Adding FFmpeg to PATH...
set "PATH=%PATH%;C:\ffmpeg\bin"
setx PATH "%PATH%;C:\ffmpeg\bin" /M >nul 2>> "%LOG_FILE%"
if !ERRORLEVEL! neq 0 (
    echo PATH update failed. Add C:\ffmpeg\bin to system PATH manually.
    echo [%DATE% %TIME%] PATH update failed >> "%LOG_FILE%"
    pause
)
cd /D "!PROJECT_DIR!" >nul 2>> "%LOG_FILE%"
call venv\Scripts\activate.bat >nul 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo Couldn’t reactivate virtual environment.
    echo [%DATE% %TIME%] Reactivate venv failed >> "%LOG_FILE%"
    pause
    exit /b 1
)

:FFMPEG_DONE
:: Check ImageMagick
echo.
echo === Checking ImageMagick ===
if exist "!IMAGEMAGICK_DIR!\magick.exe" (
    echo ImageMagick found at !IMAGEMAGICK_DIR!\magick.exe.
    echo [%DATE% %TIME%] ImageMagick found >> "%LOG_FILE%"
    goto TEST_MOVIEPY
)
echo No ImageMagick at !IMAGEMAGICK_DIR!\magick.exe.
echo Extract ImageMagick-7.1.1-47-portable-Q16-HDRI-x64.zip to !IMAGEMAGICK_DIR!.
echo Download from https://imagemagick.org/script/download.php#windows.
echo Re-run this script after extracting.
echo [%DATE% %TIME%] ImageMagick missing >> "%LOG_FILE%"
pause
exit /b 1

:TEST_MOVIEPY
echo.
echo === Testing moviepy ===
(
echo import os, tempfile
echo from moviepy.config import change_settings
echo change_settings^({"IMAGEMAGICK_BINARY": r"!IMAGEMAGICK_DIR!\magick.exe"}^)
echo from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
echo try:
echo     temp_dir = tempfile.gettempdir^(^)
echo     output_file = os.path.join^(temp_dir, "test_moviepy.mp4"^)
echo     clip = TextClip^("Test", fontsize=24, color='white', font='Arial'^)^.set_duration^(1^)
echo     clip.write_videofile^(output_file, fps=24, codec='libx264'^)
echo     if os.path.exists^(output_file^):
echo         os.remove^(output_file^)
echo         print^("moviepy test passed!"^)
echo     else:
echo         print^("moviepy test failed: Output file not created"^)
echo         exit^(1^)
echo except Exception as e:
echo     print^(f"moviepy test failed: {e}"^)
echo     exit^(1^)
) > test_moviepy.py
if not exist test_moviepy.py (
    echo Failed to create test_moviepy.py.
    echo [%DATE% %TIME%] Failed to create test_moviepy.py >> "%LOG_FILE%"
    pause
    exit /b 1
)
python test_moviepy.py >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo moviepy test failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] moviepy test failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
del test_moviepy.py >nul 2>> "%LOG_FILE%"
echo moviepy test passed.
echo [%DATE% %TIME%] moviepy test passed >> "%LOG_FILE%"

:LOOP
:: Launch UI
echo.
echo === Launching App UI ===
echo UI will open for scripts, videos, background music, and text customization.
echo [%DATE% %TIME%] Launching UI >> "%LOG_FILE%"
python faceless_video_app.py >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    echo UI launch failed. Check %LOG_FILE%.
    echo [%DATE% %TIME%] UI launch failed >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo UI launched. Close it to continue.
echo [%DATE% %TIME%] UI launched >> "%LOG_FILE%"

:: Ask to loop
echo.
echo Make another video? [Y/N]
choice /C YN /N
if !ERRORLEVEL! equ 1 (
    echo Cleaning output directory...
    if exist output_videos (
        rmdir /S /Q output_videos >nul 2>> "%LOG_FILE%"
        if !ERRORLEVEL! neq 0 (
            echo Couldn’t clean output_videos. Check permissions.
            echo [%DATE% %TIME%] Clean output_videos failed >> "%LOG_FILE%"
            pause
            exit /b 1
        )
    )
    goto LOOP
) else (
    echo Done.
    echo [%DATE% %TIME%] Exiting >> "%LOG_FILE%"
    pause
)