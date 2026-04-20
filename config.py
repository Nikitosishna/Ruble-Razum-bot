#Подтягивает настройки из .env, чтобы не писать getenv() в разных местах.

import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()


class Config:
    """
    Класс для хранения настроек проекта.
    Вместо того чтобы писать getenv(...) в разных файлах,
    мы один раз читаем всё здесь и потом импортируем config.
    """

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

    # Продакшн (Yandex Cloud)
    # REDIS_URL — Upstash Redis для хранения FSM-состояний между запросами
    # WEBHOOK_URL — HTTPS-адрес функции yc/webhook.py (из Yandex API Gateway)
    # CRON_SECRET — секрет для защиты cron-эндпоинтов yc/reminders.py и yc/results.py
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    CRON_SECRET: str = os.getenv("CRON_SECRET", "")


# Создаём объект конфигурации, который будем импортировать в проекте
config = Config()