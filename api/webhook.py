# Точка входа для Telegram-обновлений на Vercel.
# Telegram шлёт POST-запрос сюда при каждом сообщении пользователя.
# Vercel вызывает эту функцию как serverless endpoint.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from aiogram.types import Update

from bot_instance import bot, dp
from config import config
from services.db_service import init_db
from services.forecast_service import seed_meeting_dates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Запускается при старте приложения (один раз при холодном старте).
    Создаёт таблицы в БД, заполняет даты заседаний, регистрирует webhook у Telegram.
    """
    try:
        await init_db()
        await seed_meeting_dates()
        if config.WEBHOOK_URL:
            await bot.set_webhook(config.WEBHOOK_URL)
            logger.info(f"Webhook установлен: {config.WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Ошибка при старте: {e}")
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/api/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    """
    Принимает обновления от Telegram и передаёт их диспетчеру aiogram.
    Telegram ждёт ответа 200 OK — возвращаем его сразу.
    """
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.process_update(update)
    except Exception as e:
        logger.error(f"Ошибка обработки обновления: {e}")

    return JSONResponse({"ok": True})
