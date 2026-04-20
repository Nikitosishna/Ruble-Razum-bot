# Cron-обработчик итогов заседания ЦБ для Yandex Cloud Functions.
# Yandex Cloud Scheduler вызывает эту функцию каждый день в 10:30 UTC (= 13:30 МСК).

import asyncio
import logging

from bot_instance import bot
from config import config
from services.scheduler_service import send_meeting_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _handle(event: dict) -> dict:
    headers = event.get("headers", {})
    auth = headers.get("Authorization", headers.get("authorization", ""))
    if config.CRON_SECRET and auth != f"Bearer {config.CRON_SECRET}":
        return {"statusCode": 401, "body": "Unauthorized"}

    try:
        await send_meeting_results(bot)
        logger.info("Итоги заседания обработаны")
    except Exception as e:
        logger.error(f"Ошибка при рассылке итогов: {e}")

    return {"statusCode": 200, "body": "ok"}


def handler(event, context):
    """Точка входа для Yandex Cloud Functions."""
    return asyncio.run(_handle(event))
