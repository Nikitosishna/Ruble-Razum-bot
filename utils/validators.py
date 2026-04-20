# Проверка имени и email.

import re

def is_valid_name(name: str) -> bool:
    """
    Проверка имени для MVP.
    Условия:
    - строка не пустая
    - после удаления пробелов длина от 2 до 50 символов
    """

    if not name:
        return False

    name = name.strip()

    if len(name) < 2 or len(name) > 25:
        return False

    return True


def is_valid_email(email: str) -> bool:
    """
    Базовая проверка email через регулярное выражение.

    Примеры валидных значений:
    - test@gmail.com
    - user@mail.ru
    - hello@yandex.ru
    """

    if not email:
        return False

    email = email.strip().lower()

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    return bool(re.match(pattern, email))