# Файл для inline кнопок, которые появляются под текстом

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_community_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для перехода в Telegram-сообщество.

    Inline-кнопка прикрепляется к конкретному сообщению.
    При нажатии пользователь переходит по ссылке.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Рубль Разум",
                    url="https://t.me/rub_and_razum"
                )
            ]
        ]
    )


def get_currency_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Inline-клавиатура выбора валюты.

    callback_data — это специальное значение,
    которое бот получает при нажатии на inline-кнопку.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="$ Доллар 🇺🇸", callback_data="currency_usd")],
            [InlineKeyboardButton(text="€ Евро 🇪🇺", callback_data="currency_eur")],
            [InlineKeyboardButton(text="¥ Юань 🇨🇳", callback_data="currency_cny")],
            [InlineKeyboardButton(text="Đ Дирхам 🇦🇪", callback_data="currency_aed")],
            [InlineKeyboardButton(text="₺ Турецкая лира 🇹🇷", callback_data="currency_try")],
            [InlineKeyboardButton(text="£ Фунт стерлингов 🇬🇧", callback_data="currency_gbp")],
            [InlineKeyboardButton(text="₾ Грузинский лари 🇬🇪", callback_data="currency_gel")],
            [InlineKeyboardButton(text="Bitcoin 🌐", callback_data="currency_btc")],
            [InlineKeyboardButton(text="Ethereum 💠", callback_data="currency_eth")],
        ]
    )


def get_guide_payment_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопка перехода к оплате гайда.
    Пока это callback-заглушка.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти к оплате",
                    callback_data="buy_guide"
                )
            ]
        ]
    )


def get_documents_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с двумя документами:
    - политика конфиденциальности
    - оферта
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Политика конфиденциальности",
                    callback_data="open_privacy_policy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Оферта",
                    callback_data="open_offer"
                )
            ]
        ]
    )


def get_key_rate_keyboard(
    has_forecast: bool,
    is_subscribed: bool,
    has_history: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавиатура для раздела ключевой ставки.
    Показывается только когда окно прогноза открыто (за 2 дня до заседания).
    has_forecast  — пользователь уже отправил прогноз
    is_subscribed — пользователь подписан на напоминания
    has_history   — есть завершённые прогнозы (показываем кнопку статистики)
    """
    buttons = []

    if has_forecast:
        buttons.append([InlineKeyboardButton(
            text="✏️ Изменить прогноз",
            callback_data="change_forecast"
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="🎯 Сделать прогноз",
            callback_data="make_forecast"
        )])

    if not is_subscribed:
        buttons.append([InlineKeyboardButton(
            text="🔔 Напомнить о следующем прогнозе",
            callback_data="subscribe_forecast"
        )])

    if has_history:
        buttons.append([InlineKeyboardButton(
            text="📊 Моя статистика",
            callback_data="my_stats"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)