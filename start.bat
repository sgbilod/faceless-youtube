@echo off
REM ================================================
REM Faceless YouTube Automation Platform
REM Windows Launcher Script
REM ================================================

echo.
echo ================================================
echo   FACELESS YOUTUBE AUTOMATION PLATFORM
echo ================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo Checking Python version...
python --version
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
) else (
    echo WARNING: Virtual environment not found
    echo Consider creating one with: python -m venv venv
    echo.
)

REM Run the Python startup script
echo Starting all services...
echo.
python start.py

REM If script exits, show message
echo.
echo ================================================
echo   Services stopped
echo ================================================
echo.
pause
