# Единое место создания бота и диспетчера.
# Импортируется обработчиками Yandex Cloud Functions (yc/) и main.py при локальном запуске.
# В продакшне (Yandex Cloud) используется RedisStorage — FSM-состояния хранятся в Upstash Redis.
# Локально — MemoryStorage (если REDIS_URL не задан в .env).

from aiogram import Bot
from aiogram.dispatcher.dispatcher import Dispatcher

from config import config
from handlers import router


def create_bot() -> Bot:
    return Bot(token=config.BOT_TOKEN)


def create_dispatcher() -> Dispatcher:
    if config.REDIS_URL:
        # Продакшн (Yandex Cloud): FSM-состояния в Redis (Upstash)
        import redis.asyncio as aioredis
        from aiogram.fsm.storage.redis import RedisStorage

        redis_client = aioredis.from_url(config.REDIS_URL)
        storage = RedisStorage(redis_client)
    else:
        # Локально: FSM в памяти
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    return dp


# Создаются один раз при холодном старте — переиспользуются между запросами в рамках одного экземпляра
bot = create_bot()
dp = create_dispatcher()
