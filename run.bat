@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if not exist "venv\Scripts\python.exe" (
  python -m venv venv
  if errorlevel 1 goto fail
)
venv\Scripts\python.exe -c "import flask, flask_admin, flask_wtf, flask_sqlalchemy, flask_migrate, pymysql, reportlab, wtforms_sqlalchemy, user_agents, PIL" >nul 2>&1
if errorlevel 1 (
  venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
venv\Scripts\python.exe -c "from importlib.metadata import version; assert version('WTForms') == '3.1.2'" >nul 2>&1
if errorlevel 1 (
  venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
venv\Scripts\python.exe setup_local.py
if errorlevel 1 goto fail
echo.
echo Local site: http://127.0.0.1:5000
echo Demo account credentials: .local\demo-accounts.txt
echo Press Ctrl+C to stop the website. MySQL remains available on port 3307.
venv\Scripts\python.exe local_status.py
if not errorlevel 1 (
  echo Chaplin is already running. Open the address above.
  exit /b 0
)
venv\Scripts\python.exe app.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo.
echo Startup failed. Read the error above and README.md.
pause
exit /b 1
