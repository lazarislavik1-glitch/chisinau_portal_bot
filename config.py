# config.py

import os
from dotenv import load_dotenv

# Загружаем .env ТОЛЬКО если он существует (локальный запуск)
if os.path.exists(".env"):
    load_dotenv()

# Получаем переменные среды (локально — из .env, Railway — из dashboard)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
COMPANIES_FILE = "companies.json"

# Проверка токена
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден! Railway переменная BOT_TOKEN не установлена.")
