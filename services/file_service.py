# Файл для функции отправки PDF файлов, изображений пользователю в чат

from pathlib import Path
from aiogram.types import FSInputFile


BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files"

PRIVACY_POLICY_PATH = FILES_DIR / "privacy_policy.pdf"
OFFER_PATH = FILES_DIR / "offer.pdf"
COMMUNITY_IMAGE_PATH = FILES_DIR / "community_pic.png"
WHAT_CAN_BOT_IMAGE_PATH = FILES_DIR / "what_can_bot_pic.png"



def get_privacy_policy_file() -> FSInputFile:
    """
    Возвращает PDF-файл политики конфиденциальности
    для отправки в Telegram.
    """

    if not PRIVACY_POLICY_PATH.exists():
        raise FileNotFoundError(
            f"Файл политики конфиденциальности не найден: {PRIVACY_POLICY_PATH}"
        )

    return FSInputFile(
        path=str(PRIVACY_POLICY_PATH),
        filename="Политика конфиденциальности.pdf"
    )


def get_offer_file() -> FSInputFile:
    """
    Возвращает PDF-файл оферты
    для отправки в Telegram.
    """

    if not OFFER_PATH.exists():
        raise FileNotFoundError(
            f"Файл оферты не найден: {OFFER_PATH}"
        )

    return FSInputFile(
        path=str(OFFER_PATH),
        filename="Оферта.pdf"
    )


def get_community_image_file() -> FSInputFile:
    """
    Возвращает картинку сообщества для отправки в Telegram.
    """

    if not COMMUNITY_IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Файл картинки сообщества не найден: {COMMUNITY_IMAGE_PATH}"
        )

    return FSInputFile(str(COMMUNITY_IMAGE_PATH))


def get_what_can_bot_image_file() -> FSInputFile:
    """
    Возвращает картинку для раздела 'Что умеет бот?'.
    """

    if not WHAT_CAN_BOT_IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Файл картинки 'Что умеет бот?' не найден: {WHAT_CAN_BOT_IMAGE_PATH}"
        )

    return FSInputFile(str(WHAT_CAN_BOT_IMAGE_PATH))