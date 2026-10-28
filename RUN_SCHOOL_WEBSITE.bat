@echo off
setlocal
cd /d "%~dp0"
title Kikandwa Community Secondary School Website Server
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found.
  echo Install Python 3.11 or newer from https://www.python.org/downloads/windows/
  echo During installation, tick "Add Python to PATH".
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating the website's private Python environment...
  py -m venv .venv
  if errorlevel 1 goto failed
)
echo [2/3] Installing required website packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo [3/3] Starting Kikandwa Community Secondary School website...
echo.
echo Keep this black window OPEN while using the website.
echo Website: http://127.0.0.1:5000/
echo Parent Portal: http://127.0.0.1:5000/portal.html
echo Admin: http://127.0.0.1:5000/admin.html
echo Press Ctrl+C to stop the server.
start "" http://127.0.0.1:5000/
".venv\Scripts\python.exe" app.py
pause
exit /b 0
:failed
echo.
echo SETUP FAILED. Read the red error above. Check your internet connection and install Python 3.11+.
pause
exit /b 1
