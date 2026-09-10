import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler

from bot_instance import bot
from services.db_service import get_payment_by_payment_id, update_payment_status
from services.file_service import get_guide_file
from services.payment_service import get_payment_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


async def _handle_payment(body: bytes) -> None:
    data = json.loads(body)
    event_type = data.get("event", "")
    payment_obj = data.get("object", {})
    payment_id = payment_obj.get("id")

    if event_type != "payment.succeeded" or not payment_id:
        return

    payment_info = await get_payment_status(payment_id)
    if payment_info.get("status") != "succeeded":
        return

    payment_record = await get_payment_by_payment_id(payment_id)
    if not payment_record:
        logger.warning(f"Платёж {payment_id} не найден в БД")
        return

    if payment_record.status == "succeeded":
        logger.info(f"Платёж {payment_id} уже обработан")
        return

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
    await bot.send_document(chat_id=payment_record.telegram_user_id, document=guide_file)
    logger.info(f"Гайд отправлен пользователю {payment_record.telegram_user_id}")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            _loop.run_until_complete(_handle_payment(body))
        except Exception as e:
            logger.error(f"Ошибка в webhook ЮKassa: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass
