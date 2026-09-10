import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler

# Event loop must be set before importing bot_instance so the Redis client
# is created on the same loop we will use in _loop.run_until_complete()
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

from aiogram.types import Update
from bot_instance import bot, dp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            update = Update.model_validate(json.loads(body))
            _loop.run_until_complete(dp.feed_update(bot=bot, update=update))
        except Exception as e:
            logger.error(f"Ошибка обработки обновления: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK - bot running')

    def log_message(self, *args):
        pass
