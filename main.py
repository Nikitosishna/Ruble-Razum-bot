# Точка входа для локального запуска бота в режиме polling.
# В продакшне (Yandex Cloud) бот запускается через обработчики в папке yc/:
#   yc/webhook.py    — приём обновлений от Telegram
#   yc/payment.py    — webhook ЮKassa для автодоставки гайда
#   yc/reminders.py  — ежедневные напоминания о прогнозе (Yandex Cloud Scheduler, 10:00 МСК)
#   yc/results.py    — рассылка итогов заседания ЦБ (Yandex Cloud Scheduler, 13:30 МСК)
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from handlers import router
from services.db_service import init_db
from services.forecast_service import seed_meeting_dates
# APScheduler используется только при локальном запуске.
# В продакшне (Yandex Cloud) расписание выполняется через Yandex Cloud Scheduler → yc/reminders.py, yc/results.py
try:
    from services.scheduler_service import start_scheduler
    _scheduler_available = True
except ImportError:
    _scheduler_available = False


async def main() -> None:
    """
    Главная функция запуска проекта.
    Что здесь происходит:
    1. Проверка наличия токена и ссылки подключения к БД
    2. Создание объекта бота
    3. Создание Dispatcher
    4. Подключение к роутер
    5. Инициализация таблицы БД
    6. Запуск polling
    """

    if not config.BOT_TOKEN:
        raise ValueError("В .env не найден BOT_TOKEN")

    if not config.DATABASE_URL:
        raise ValueError("В .env не найден DATABASE_URL")


    #Логи, чтобы не выходило "Forcing soap:address location to HTTPS"
    # лишние warning-сообщения zeep в консоли
    logging.getLogger("zeep").setLevel(logging.ERROR)
    logging.getLogger("zeep.wsdl.bindings.soap").setLevel(logging.ERROR)


    # Bot — основной объект Telegram-бота
    bot = Bot(token=config.BOT_TOKEN)

    # MemoryStorage хранит FSM-состояния в памяти процесса.
    # При локальном запуске этого достаточно — процесс живёт постоянно.
    # В продакшне (Yandex Cloud) используется Redis через bot_instance.py.
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    # Создаём таблицы в базе, если они ещё не созданы
    await init_db()

    # Заполняем даты заседаний ЦБ при первом запуске (если таблица пуста)
    await seed_meeting_dates()

    # Запускаем планировщик (только локально; в продакшне заменён Yandex Cloud Scheduler)
    if _scheduler_available:
        start_scheduler(bot)

    print("Бот запущен")

    # Запускаем long polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())