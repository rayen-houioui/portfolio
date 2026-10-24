@echo off
REM Lance ProfilPro RH en une fois (Windows). Prérequis : Python 3.10+ installé (case "Add to PATH" cochée).
cd /d "%~dp0"
if not exist frontend\dist\index.html ( pushd frontend & call npm install & call npm run build & popd )
if not exist .venv ( python -m venv .venv )
call .venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py setup_data
if not exist models\xgboost_hours.pkl ( python manage.py train_hours )
echo.
echo ==> Ouvrez http://127.0.0.1:8000 dans votre navigateur
python manage.py runserver
pause
