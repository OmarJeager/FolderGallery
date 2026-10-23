@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install requirements. Install Python 3.10+ and try again.
  pause
  exit /b 1
)
py -3 main.py
pause
