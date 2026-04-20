#Здесь будут кнопки главного меню:
#Старт
#Купить гайд
#Сообщество Рубль-Разум
#Актуальные курсы валют
#Текущая ключевая ставка ЦБ РФ
#Что умеет бот?

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Основная клавиатура бота.
    Показывается после завершения регистрации.

    """

    keyboard = [
        [
            KeyboardButton(text="Купить гайд")
        ],
        [
            KeyboardButton(text="Ключевая ставка ЦБ РФ"),
            KeyboardButton(text="Актуальные курсы валют")
        ],
        [

            KeyboardButton(text="Сообщество"),
            KeyboardButton(text="Что умеет бот?")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )