#!/usr/bin/env bash
# Lance ProfilPro RH en une fois (macOS / Linux). Prérequis : Python 3.10+
cd "$(dirname "$0")"
[ -f frontend/dist/index.html ] || (cd frontend && npm install && npm run build)
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py setup_data
[ -f models/xgboost_hours.pkl ] || python manage.py train_hours
echo "==> Ouvrez http://127.0.0.1:8000"
python manage.py runserver
