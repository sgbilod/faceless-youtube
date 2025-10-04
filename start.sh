#!/bin/bash
# ================================================
# Faceless YouTube Automation Platform
# Linux/Mac Launcher Script
# ================================================

echo ""
echo "================================================"
echo "  FACELESS YOUTUBE AUTOMATION PLATFORM"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python not found"
    echo "Please install Python 3.8+ from https://www.python.org/"
    echo ""
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# Display Python version
echo "Checking Python version..."
$PYTHON_CMD --version
echo ""

# Activate virtual environment if it exists
if [ -f venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo ""
else
    echo "WARNING: Virtual environment not found"
    echo "Consider creating one with: python -m venv venv"
    echo ""
fi

# Run the Python startup script
echo "Starting all services..."
echo ""
$PYTHON_CMD start.py

# If script exits, show message
echo ""
echo "================================================"
echo "  Services stopped"
echo "================================================"
echo ""
