# Cron-обработчик напоминаний для Yandex Cloud Functions.
# Yandex Cloud Scheduler вызывает эту функцию каждый день в 07:00 UTC (= 10:00 МСК).

import asyncio
import logging

from bot_instance import bot
from config import config
from services.scheduler_service import send_forecast_reminders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _handle(event: dict) -> dict:
    # Проверяем CRON_SECRET если задан
    headers = event.get("headers", {})
    auth = headers.get("Authorization", headers.get("authorization", ""))
    if config.CRON_SECRET and auth != f"Bearer {config.CRON_SECRET}":
        return {"statusCode": 401, "body": "Unauthorized"}

    try:
        await send_forecast_reminders(bot)
        logger.info("Напоминания отправлены")
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")

    return {"statusCode": 200, "body": "ok"}


def handler(event, context):
    """Точка входа для Yandex Cloud Functions."""
    return asyncio.run(_handle(event))
