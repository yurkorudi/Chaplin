@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
venv\Scripts\python.exe -m pytest -q
exit /b %errorlevel%
