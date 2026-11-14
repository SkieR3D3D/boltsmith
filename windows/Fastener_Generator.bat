@echo off
rem Fastener generator -> STEP with real threads. First start downloads the CAD kernel (once).
cd /d %~dp0
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul || (
  echo Installing uv...
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)
echo Starting fastener generator...
uv run --python 3.12 --with build123d==0.13.0 --with bd_warehouse==0.4.0 python fastener_gui.py
if errorlevel 1 pause
