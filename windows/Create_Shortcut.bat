@echo off
rem Creates Boltsmith shortcuts on the Desktop and in the Start menu
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make_shortcut.ps1"
pause
