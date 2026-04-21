#файл для API запроса ключевой ставки от cbr.ru

import asyncio
from datetime import datetime, timedelta

from zeep import Client
from zeep.transports import Transport

from config import config

WSDL_URL = "https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL"

CACHE_KEY = "cbr_key_rate"
CACHE_TTL = 2 * 3600  # 2 часа


async def _get_redis():
    """Возвращает Redis-клиент если REDIS_URL задан, иначе None (локальный запуск)."""
    if not config.REDIS_URL:
        return None
    import redis.asyncio as aioredis
    return aioredis.from_url(config.REDIS_URL)


async def invalidate_rate_cache() -> None:
    """Сбрасывает кэш ключевой ставки. Вызывается после рассылки итогов заседания."""
    redis = await _get_redis()
    if redis:
        await redis.delete(CACHE_KEY)

# Кэш клиента zeep — создаётся один раз, переиспользуется в рамках одного экземпляра функции
_cbr_client = None


def _get_cbr_client():
    global _cbr_client
    if _cbr_client is None:
        transport = Transport(timeout=15)
        _cbr_client = Client(wsdl=WSDL_URL, transport=transport)
    return _cbr_client


def _extract_rate_from_lxml_element(root_element) -> str:
    """
    Достаёт актуальную ключевую ставку из XML-ответа ЦБ.

    В ответе KeyRateXML ставки идут от более новых дат к более старым,
    поэтому берём первую найденную ставку.
    """

    rates = []

    for element in root_element.iter():
        tag_name = element.tag

        if isinstance(tag_name, str) and "}" in tag_name:
            tag_name = tag_name.split("}", 1)[1]

        if tag_name == "Rate" and element.text:
            rates.append(element.text.strip())

    if not rates:
        raise RuntimeError("Не удалось найти значение ключевой ставки в XML ЦБ.")

    return rates[0].replace(".", ",")


async def fetch_key_rate() -> str:
    """
    Получает ключевую ставку ЦБ РФ через официальный SOAP/WSDL-сервис ЦБ
    методом KeyRateXML.
    """

    today = datetime.now().astimezone()
    from_date = today - timedelta(days=30)

    for attempt in range(3):
        try:
            def _load_rate():
                client = _get_cbr_client()
                result = client.service.KeyRateXML(from_date, today)

                if result is None:
                    raise RuntimeError("ЦБ вернул пустой ответ.")

                return _extract_rate_from_lxml_element(result)

            return await asyncio.to_thread(_load_rate)

        except Exception as e:
            print("Ошибка при получении ключевой ставки через zeep:", repr(e))

            if attempt == 2:
                raise RuntimeError(
                    "Не удалось получить данные от ЦБ прямо сейчас.\nПопробуйте через пару минут."
                )

            await asyncio.sleep(1)


async def get_key_rate_text() -> str:
    redis = await _get_redis()

    # Проверяем кэш
    if redis:
        cached = await redis.get(CACHE_KEY)
        if cached:
            rate = cached.decode()
            return f"Текущая ключевая ставка — <b>{rate}</b>%"

    # Кэша нет — идём к ЦБ
    rate = await fetch_key_rate()

    # Сохраняем в Redis на 2 часа
    if redis:
        await redis.set(CACHE_KEY, rate, ex=CACHE_TTL)

    return f"Текущая ключевая ставка — <b>{rate}</b>%"