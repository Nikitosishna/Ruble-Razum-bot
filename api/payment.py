import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

from bot_instance import bot
from services.db_service import get_payment_by_payment_id, update_payment_status, mark_guide_delivered
from services.file_service import get_guide_file, GUIDE_COVER_IMAGE_PATH, get_guide_cover_image_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _handle_payment(body: bytes) -> None:
    data = json.loads(body)
    event_type = data.get("event", "")
    payment_obj = data.get("object", {})
    payment_id = payment_obj.get("id")
    # Статус прямо из тела вебхука — не делаем лишний запрос к ЮKassa API
    payment_status = payment_obj.get("status")

    logger.info(f"Webhook: event={event_type}, payment_id={payment_id}, status={payment_status}")

    if event_type != "payment.succeeded" or not payment_id:
        return

    if payment_status != "succeeded":
        logger.warning(f"Неожиданный статус в вебхуке: {payment_status}")
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
            "💳 Оплата прошла успешно!\n\n"
            "Отправляю гайд.\n\n"
            "Поздравляю — вы сделали первый шаг к более осознанному "
            "управлению своими финансами."
        )
    )
    guide_file = get_guide_file()
    await bot.send_document(chat_id=payment_record.telegram_user_id, document=guide_file)
    await mark_guide_delivered(payment_id)
    logger.info(f"Гайд отправлен пользователю {payment_record.telegram_user_id}")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            _loop.run_until_complete(_handle_payment(body))
        except Exception as e:
            logger.error(f"Ошибка в webhook ЮKassa: {type(e).__name__}: {e}", exc_info=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass
