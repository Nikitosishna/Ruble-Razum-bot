# Webhook от ЮKassa — автоматическая доставка гайда после оплаты.
# ЮKassa шлёт POST-запрос сюда при успешной оплате.

import asyncio
import base64
import json
import logging

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

from bot_instance import bot
from services.payment_service import get_payment_status
from services.db_service import get_payment_by_payment_id, update_payment_status
from services.file_service import get_guide_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _handle(event: dict) -> dict:
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        data = json.loads(body)
        event_type = data.get("event", "")
        payment_obj = data.get("object", {})
        payment_id = payment_obj.get("id")

        if event_type != "payment.succeeded" or not payment_id:
            return {"statusCode": 200, "body": "ok"}

        # Перепроверяем статус через ЮKassa API
        payment_info = await get_payment_status(payment_id)
        if payment_info.get("status") != "succeeded":
            return {"statusCode": 200, "body": "ok"}

        payment_record = await get_payment_by_payment_id(payment_id)
        if not payment_record:
            logger.warning(f"Платёж {payment_id} не найден в БД")
            return {"statusCode": 200, "body": "ok"}

        # Защита от дублей
        if payment_record.status == "succeeded":
            logger.info(f"Платёж {payment_id} уже обработан")
            return {"statusCode": 200, "body": "ok"}

        await update_payment_status(payment_id, "succeeded")

        await bot.send_message(
            chat_id=payment_record.telegram_user_id,
            text=(
                "💳 Оплата прошла успешно! Отправляю гайд.\n\n"
                "Поздравляю — вы сделали первый шаг к более осознанному "
                "управлению своими финансами."
            )
        )
        guide_file = get_guide_file()
        await bot.send_document(
            chat_id=payment_record.telegram_user_id,
            document=guide_file
        )
        logger.info(f"Гайд отправлен пользователю {payment_record.telegram_user_id}")

    except Exception as e:
        logger.error(f"Ошибка в webhook ЮKassa: {e}")

    return {"statusCode": 200, "body": "ok"}


def handler(event, context):
    """Точка входа для Yandex Cloud Functions."""
    return _loop.run_until_complete(_handle(event))
