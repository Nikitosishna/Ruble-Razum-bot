# Обработчик Telegram-обновлений для Yandex Cloud Functions.
# Telegram шлёт POST-запрос сюда при каждом сообщении пользователя.

import asyncio
import base64
import json
import logging

from aiogram.types import Update

from bot_instance import bot, dp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


async def _handle(event: dict) -> dict:
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
    return _loop.run_until_complete(_handle(event))
