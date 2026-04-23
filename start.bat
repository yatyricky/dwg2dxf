@echo off
chcp 65001 >nul
cd /d "%~dp0"
python gui.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start GUI.
    echo Make sure Python 3 is installed and in PATH.
    pause
)
