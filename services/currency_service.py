#Файл для API запросов к ЦБ РФ и Binance

import asyncio
import xml.etree.ElementTree as ET

import httpx


CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"

FIAT_CODES = {"USD", "EUR", "CNY", "AED", "TRY", "GBP", "GEL", "BYN", "CHF"}


async def fetch_cbr_rates() -> dict[str, dict]:
    """
    Получает актуальные курсы валют с сайта ЦБ РФ.
    ЦБ возвращает XML.
    Мы преобразуем его в словарь такого вида:
    {
        "USD": {"value": 91.2345, "nominal": 1, "name": "Доллар США"},
        "EUR": {"value": 99.8765, "nominal": 1, "name": "Евро"},
        ...
    }

    Если запрос не удался, делаем до 3 попыток.
    """

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(CBR_DAILY_URL)
                response.raise_for_status()

            root = ET.fromstring(response.text)
            rates = {}

            for valute in root.findall("Valute"):
                char_code = valute.findtext("CharCode")
                nominal = valute.findtext("Nominal")
                name = valute.findtext("Name")
                value = valute.findtext("Value")

                if not char_code or not nominal or not name or not value:
                    continue

                rates[char_code] = {
                    "value": float(value.replace(",", ".")),
                    "nominal": int(nominal),
                    "name": name
                }

            return rates

        except Exception:
            if attempt == 2:
                raise RuntimeError(
                    "Не удалось получить данные от ЦБ.\nПопробуйте через пару минут."
                )
            await asyncio.sleep(1)


async def get_fiat_rate(char_code: str) -> str:
    """
    Возвращает готовую строку с курсом фиатной валюты.

    Примеры:
    $ Доллар USD: 81,5 ₽
    ¥ Юань CNY: 11,4 ₽
    £ Фунт стерлингов GBP: 104,5 ₽
    """

    char_code = char_code.upper()

    if char_code not in FIAT_CODES:
        raise ValueError(f"Неподдерживаемая валюта: {char_code}")

    rates = await fetch_cbr_rates()

    if char_code not in rates:
        raise RuntimeError("Не удалось найти нужную валюту в ответе ЦБ.")

    currency = rates[char_code]
    value = currency["value"]
    nominal = currency["nominal"]

    # Если номинал не 1, приводим курс к 1 единице валюты
    value_per_one = value / nominal

    currency_map = {
        "USD": "Доллар 🇺🇸",
        "EUR": "Евро 🇪🇺",
        "CNY": "Юань 🇨🇳",
        "AED": "Дирхам 🇦🇪",
        "TRY": "Турецкая лира 🇹🇷",
        "GBP": "Фунт стерлингов 🇬🇧",
        "GEL": "Грузинский лари 🇬🇪",
        "BYN": "Белорусский рубль 🇧🇾",
        "CHF": "Швейцарский франк 🇨🇭",
    }

    title = currency_map[char_code]

    # 1 знак после запятой и замена точки на запятую
    formatted_value = f"{value_per_one:.1f}".replace(".", ",")

    return f"{title}: {formatted_value} ₽"


async def fetch_binance_price(symbol: str) -> float:
    """
    Получает последнюю цену инструмента с Binance.
    Например:
    - BTCUSDT
    - ETHUSDT
    """

    params = {"symbol": symbol.upper()}

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(BINANCE_TICKER_URL, params=params)
                response.raise_for_status()

            data = response.json()
            return float(data["price"])

        except Exception:
            if attempt == 2:
                raise RuntimeError(
                    "Курс криптовалюты временно недоступен. Попробуйте позже."
                )
            await asyncio.sleep(1)


def format_number_with_commas(value: float) -> str:
    """
    Форматирует число без знаков после запятой
    и с запятыми между тысячами.
    Пример:
    71750 -> '71,750'
    """

    return f"{value:,.0f}"


async def get_crypto_rate(code: str) -> str:
    """
    Возвращает курс криптовалюты в долларах и рублях.
    Формат:
    Bitcoin: 71,750 $ / 5,584,776 ₽
    """

    code = code.upper()

    rates = await fetch_cbr_rates()

    if "USD" not in rates:
        raise RuntimeError("Не удалось получить курс доллара из ЦБ.")

    usd_rub = rates["USD"]["value"]

    if code == "BTC":
        price_usd = await fetch_binance_price("BTCUSDT")
        price_rub = price_usd * usd_rub

        return f"Bitcoin 🌐: {format_number_with_commas(price_usd)} $ / {format_number_with_commas(price_rub)} ₽"

    if code == "ETH":
        price_usd = await fetch_binance_price("ETHUSDT")
        price_rub = price_usd * usd_rub

        return f"Ethereum 💠: {format_number_with_commas(price_usd)} $ / {format_number_with_commas(price_rub)} ₽"

    raise ValueError(f"Неподдерживаемая криптовалюта: {code}")