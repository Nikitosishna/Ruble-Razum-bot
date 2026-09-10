import asyncio
import logging
from http.server import BaseHTTPRequestHandler

from bot_instance import bot
from config import config
from services.scheduler_service import send_meeting_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        auth = self.headers.get('Authorization', '')
        if config.CRON_SECRET and auth != f'Bearer {config.CRON_SECRET}':
            self.send_response(401)
            self.end_headers()
            return
        try:
            _loop.run_until_complete(send_meeting_results(bot))
            logger.info("Итоги заседания обработаны")
        except Exception as e:
            logger.error(f"Ошибка при рассылке итогов: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass
