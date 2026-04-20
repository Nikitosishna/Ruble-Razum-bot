# Обработчик Telegram-обновлений для Yandex Cloud Functions.
# Telegram шлёт POST-запрос сюда при каждом сообщении пользователя.

import asyncio
import base64
import json
import logging

from aiogram.types import Update

from bot_instance import bot, dp
from config import config
from services.db_service import init_db
from services.forecast_service import seed_meeting_dates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Флаг инициализации — выполняется один раз на "тёплый" экземпляр функции
_initialized = False


async def _init():
    global _initialized
    if not _initialized:
        await init_db()
        await seed_meeting_dates()
        if config.WEBHOOK_URL:
            await bot.set_webhook(config.WEBHOOK_URL)
            logger.info(f"Webhook установлен: {config.WEBHOOK_URL}")
        _initialized = True


async def _handle(event: dict) -> dict:
    await _init()

    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        data = json.loads(body)
        update = Update.model_validate(data)
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error(f"Ошибка обработки обновления: {e}")

    return {"statusCode": 200, "body": "ok"}


def handler(event, context):
    """Точка входа для Yandex Cloud Functions."""
    return asyncio.run(_handle(event))
