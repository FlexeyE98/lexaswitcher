@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%START_LEXA_SWITCHER_850k.ps1" -ProjectRoot "%SCRIPT_DIR%.."
