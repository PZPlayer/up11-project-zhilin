"""Настройки приложения «Мир гаджетов»."""
import os
from pathlib import Path

APP_TITLE = "Мир гаджетов"
APP_DIR = Path(__file__).resolve().parent
RES_DIR = APP_DIR.parent / "resources"
IMAGES_DIR = RES_DIR / "Images"
LOGO_PATH = RES_DIR / "logo.png"
ICON_PATH = RES_DIR / "icon.ico"
PLACEHOLDER_PATH = RES_DIR / "picture.png"

# Параметры подключения к PostgreSQL. Можно переопределить переменными окружения
# (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD), чтобы не хранить пароль в коде.
DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "gadgets_db"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "224466"),
}
