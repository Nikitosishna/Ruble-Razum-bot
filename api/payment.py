# Webhook от ЮKassa — автоматическая доставка гайда после оплаты.
# ЮKassa шлёт POST-запрос сюда при изменении статуса платежа.
# Мы перепроверяем статус через API (не доверяем телу запроса),
# находим пользователя и отправляем ему PDF.

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bot_instance import bot
from services.payment_service import get_payment_status
from services.db_service import get_payment_by_payment_id, update_payment_status
from services.file_service import get_offer_file

logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/api/payment")
async def yookassa_webhook(request: Request) -> JSONResponse:
    """
    Обрабатывает уведомление от ЮKassa.
    Всегда возвращает 200 — иначе ЮKassa будет повторять запросы.
    """
    try:
        data = await request.json()
        event = data.get("event", "")
        payment_obj = data.get("object", {})
        payment_id = payment_obj.get("id")

        # Нас интересует только успешная оплата
        if event != "payment.succeeded" or not payment_id:
            return JSONResponse({"ok": True})

        # Перепроверяем статус через ЮKassa API (защита от подделки запроса)
        payment_info = await get_payment_status(payment_id)
        if payment_info.get("status") != "succeeded":
            return JSONResponse({"ok": True})

        # Ищем платёж в нашей БД
        payment_record = await get_payment_by_payment_id(payment_id)
        if not payment_record:
            logger.warning(f"Платёж {payment_id} не найден в БД")
            return JSONResponse({"ok": True})

        # Защита от дублей: если уже обработали — пропускаем
        if payment_record.status == "succeeded":
            logger.info(f"Платёж {payment_id} уже обработан, пропускаем")
            return JSONResponse({"ok": True})

        # Помечаем как обработанный
        await update_payment_status(payment_id, "succeeded")

        # Отправляем гайд пользователю
        await bot.send_message(
            chat_id=payment_record.telegram_user_id,
            text=(
                "💳 Оплата прошла успешно! Отправляю гайд.\n\n"
                "Поздравляю — вы сделали первый шаг к более осознанному "
                "управлению своими финансами."
            )
        )
        guide_file = get_offer_file()  # ← заменишь на реальный файл гайда
        await bot.send_document(
            chat_id=payment_record.telegram_user_id,
            document=guide_file
        )
        logger.info(f"Гайд отправлен пользователю {payment_record.telegram_user_id}")

    except Exception as e:
        logger.error(f"Ошибка в webhook ЮKassa: {e}")

    return JSONResponse({"ok": True})
