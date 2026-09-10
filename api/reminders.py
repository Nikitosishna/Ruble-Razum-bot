import asyncio
import logging
from http.server import BaseHTTPRequestHandler

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

from bot_instance import bot
from config import config
from services.scheduler_service import send_forecast_reminders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        auth = self.headers.get('Authorization', '')
        if config.CRON_SECRET and auth != f'Bearer {config.CRON_SECRET}':
            self.send_response(401)
            self.end_headers()
            return
        try:
            _loop.run_until_complete(send_forecast_reminders(bot))
            logger.info("Напоминания отправлены")
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass
