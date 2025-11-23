import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
COMPANIES_FILE = "companies.json"

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN отсутствует в .env!")
