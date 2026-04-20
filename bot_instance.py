# Единое место создания бота и диспетчера.
# Импортируется всеми api-функциями на Vercel и main.py локально.
# На Vercel используется RedisStorage (Upstash).
# Локально — MemoryStorage (если REDIS_URL не задан).

from aiogram import Bot
from aiogram.dispatcher.dispatcher import Dispatcher

from config import config
from handlers import router


def create_bot() -> Bot:
    return Bot(token=config.BOT_TOKEN)


def create_dispatcher() -> Dispatcher:
    if config.REDIS_URL:
        # Продакшн: FSM-состояния в Redis (Upstash)
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


# Создаём один раз при холодном старте — переиспользуются между запросами
bot = create_bot()
dp = create_dispatcher()
