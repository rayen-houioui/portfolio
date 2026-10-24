import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(path):
    """Lit un fichier .env (CLE=valeur) sans dépendance ; les variables déjà définies ne sont pas écrasées."""
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env_file(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = ["django.contrib.staticfiles", "segmentation"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
# Base de données : DB_ENGINE=auto (défaut) -> MySQL/MariaDB de XAMPP s'il est joignable (la base est créée au besoin),
# sinon SQLite automatiquement (aucune installation requise). Forcer avec DB_ENGINE=mysql ou DB_ENGINE=sqlite.
_DB = {"NAME": os.getenv("DB_NAME", "profilpro"), "USER": os.getenv("DB_USER", "root"),
       "PASSWORD": os.getenv("DB_PASSWORD", ""), "HOST": os.getenv("DB_HOST", "127.0.0.1"), "PORT": os.getenv("DB_PORT", "3306")}


def _mysql_available() -> bool:
    try:
        import pymysql

        conn = pymysql.connect(host=_DB["HOST"], port=int(_DB["PORT"]), user=_DB["USER"], password=_DB["PASSWORD"],
                               connect_timeout=2)
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{_DB['NAME']}` CHARACTER SET utf8mb4")
        conn.close()
        return True
    except Exception:
        return False


_ENGINE = os.getenv("DB_ENGINE", "auto").lower()
if _ENGINE == "auto":
    _ENGINE = "mysql" if _mysql_available() else "sqlite"
    if _ENGINE == "sqlite" and os.getenv("RUN_MAIN") != "true":
        print("[ProfilPro] MySQL/MariaDB indisponible : utilisation de SQLite (db.sqlite3).")
if _ENGINE == "mysql":
    DATABASES = {"default": {"ENGINE": "django.db.backends.mysql", **_DB, "OPTIONS": {"charset": "utf8mb4"}}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
LANGUAGE_CODE = "fr-fr"
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Modèle de segmentation (back-end) et build du front-end Figma (React/Vite)
MODEL_PATH = BASE_DIR / "models" / "modele_profilpro.pkl"
# Classification des revenus (CatBoost) — requiert le paquet « catboost » (voir requirements.txt)
INCOME_MODEL_PATH = BASE_DIR / "models" / "catboost_adult.pkl"
HOURS_MODEL_PATH = BASE_DIR / "models" / "xgboost_hours.pkl"  # régression des heures (créé automatiquement au besoin)
# Prédiction de la catégorie de poste (CatBoost fourni par l'utilisateur)
OCCUPATION_MODEL_PATH = BASE_DIR / "models" / "catboost_model.pkl"
OCCUPATION_FEATURES_PATH = BASE_DIR / "models" / "catboost_features.pkl"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

