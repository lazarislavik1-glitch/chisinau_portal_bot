
# web/api.py
import asyncio

from fastapi import FastAPI, Request
from telegram import Update

from bot import create_application

app = FastAPI()

# Создаём одно приложение Telegram на весь процесс
application = create_application()


@app.on_event("startup")
async def on_startup():
    # Инициализация Telegram-приложения
    await application.initialize()
    await application.start()
    print("✅ Telegram Application started (webhook mode).")


@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()
    print("🛑 Telegram Application stopped.")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Chisinau-PORTAL API работает"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Эндпоинт, куда Telegram будет слать обновления."""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    # Передаём update в PTB
    await application.process_update(update)
    return {"ok": True}

