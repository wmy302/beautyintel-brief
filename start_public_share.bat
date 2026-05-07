@echo off
setlocal
cd /d "%~dp0"
set /p NGROK_TOKEN=Paste ngrok authtoken, or press Enter if already configured: 
powershell -ExecutionPolicy Bypass -File ".\scripts\start_public_share.ps1" -Authtoken "%NGROK_TOKEN%"
pause
