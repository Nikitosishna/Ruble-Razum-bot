# Обработчики курсов валют.
# Фиатные валюты (ЦБ РФ) и криптовалюты (Binance).

from aiogram import Router
from aiogram.types import Message, CallbackQuery

from keyboards.reply import get_main_keyboard
from keyboards.inline import get_currency_inline_keyboard
from services.currency_service import get_fiat_rate, get_crypto_rate

router = Router()

# callback_data → код валюты для get_fiat_rate()
FIAT_CURRENCY_MAP = {
    "currency_usd": "USD",
    "currency_eur": "EUR",
    "currency_cny": "CNY",
    "currency_aed": "AED",
    "currency_try": "TRY",
    "currency_gbp": "GBP",
    "currency_gel": "GEL",
    "currency_byn": "BYN",
    "currency_chf": "CHF",
}

# callback_data → код для get_crypto_rate()
CRYPTO_CURRENCY_MAP = {
    "currency_btc": "BTC",
    "currency_eth": "ETH",
}


@router.message(lambda message: message.text == "Актуальные курсы валют")
async def currency_handler(message: Message) -> None:
    """Показывает inline-клавиатуру выбора валюты."""
    await message.answer(
        "Выбери валюту, чтобы узнать актуальный курс:",
        reply_markup=get_currency_inline_keyboard()
    )


@router.callback_query(lambda c: c.data in FIAT_CURRENCY_MAP)
async def process_fiat_callback(callback: CallbackQuery) -> None:
    """Универсальный обработчик фиатных валют."""
    code = FIAT_CURRENCY_MAP[callback.data]
    try:
        rate_text = await get_fiat_rate(code)
        await callback.message.answer(rate_text, reply_markup=get_main_keyboard())
    except Exception as e:
        await callback.message.answer(str(e))
    await callback.answer()


@router.callback_query(lambda c: c.data in CRYPTO_CURRENCY_MAP)
async def process_crypto_callback(callback: CallbackQuery) -> None:
    """Универсальный обработчик криптовалют."""
    code = CRYPTO_CURRENCY_MAP[callback.data]
    try:
        rate_text = await get_crypto_rate(code)
        await callback.message.answer(rate_text, reply_markup=get_main_keyboard())
    except Exception as e:
        await callback.message.answer(str(e))
    await callback.answer()
