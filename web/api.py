# web/api.py

import asyncio
from fastapi import FastAPI, Request
from telegram import Update

from bot import create_app

app = FastAPI()

# Создаём Telegram Application одно на весь сервер
application = create_app()


@app.on_event("startup")
async def on_startup():
    """Запускаем Telegram-бота при запуске Railway."""
    await application.initialize()
    await application.start()
    print("✅ Telegram bot started in WEBHOOK MODE")


@app.on_event("shutdown")
async def on_shutdown():
    """Корректная остановка."""
    await application.stop()
    await application.shutdown()
    print("🛑 Telegram bot stopped")


@app.get("/")
async def root():
    return {"status": "ok", "message": "API работает"}


@app.post("/webhook")
async def webhook(request: Request):
    """Telegram отправляет обновления сюда."""
    data = await request.json()

    update = Update.de_json(data, application.bot)

    # Передаём обновление в Telegram bot
    await application.process_update(update)

    return {"ok": True}
