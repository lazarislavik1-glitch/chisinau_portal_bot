from fastapi import FastAPI, Request
import json
import asyncio
from bot import application  # импорт нашего Telegram-бота

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "API работает"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    # Передаём обновление в Telegram bot application
    update = application.update_queue
    await update.put(data)

    return {"status": "received"}
