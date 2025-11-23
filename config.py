# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора (число)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Путь к файлу с компаниями
COMPANIES_FILE = os.path.join(
    os.path.dirname(__file__),
    "companies.json"
)

# Проверка, что токен задан
if not BOT_TOKEN:
    raise RuntimeError("❌ В .env не указан BOT_TOKEN")

