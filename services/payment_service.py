# Сервис для работы с платежами через ЮKassa API.
# Создаёт платежи и получает ссылки на оплату.

import httpx
import uuid
from config import config

YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"


async def create_payment(
        amount: float,
        description: str = "Гайд по финансовой грамотности",
        return_url: str = "https://example.com/success"  # после оплаты вернётся сюда
) -> dict:
    """
    Создаёт платёж в ЮKassa.
    Возвращает словарь с payment_id и confirmation_url (ссылка на оплату).
    """

    # Уникальный ключ для защиты от дублей (если нажать кнопку дважды)
    idempotence_key = str(uuid.uuid4())

    # Данные платежа
    payload = {
        "amount": {
            "value": str(amount),  # сумма
            "currency": "RUB"  # российские рубли
        },
        "capture": True,  # ← вот эта строка! автосписание без подтверждения
        "confirmation": {
            "type": "redirect",  # тип: редирект на оплату
            "return_url": return_url
        },
        "description": description,
        "metadata": {
            "order_id": idempotence_key
        }
    }

    # Заголовки для запроса
    headers = {
        "Idempotence-Key": idempotence_key,
        "Content-Type": "application/json"
    }

    # Отправляем запрос к ЮKassa
    async with httpx.AsyncClient() as client:
        response = await client.post(
            YOOKASSA_API_URL,
            json=payload,
            headers=headers,
            auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY),
            timeout=10.0
        )

    # Проверяем, успешен ли запрос
    if response.status_code in [200, 201]:
        data = response.json()
        return {
            "payment_id": data.get("id"),
            "confirmation_url": data.get("confirmation", {}).get("confirmation_url"),
            "status": data.get("status")
        }
    else:
        # Если ошибка — возвращаем её
        raise Exception(f"ЮKassa error: {response.status_code} - {response.text}")


async def get_payment_status(payment_id: str) -> dict:
    """
    Проверяет статус платежа в ЮKassa по payment_id.
    Возвращает информацию о статусе платежа.
    """

    url = f"{YOOKASSA_API_URL}/{payment_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY),
            timeout=10.0
        )

    if response.status_code == 200:
        data = response.json()
        return {
            "payment_id": data.get("id"),
            "status": data.get("status"),  # "pending", "succeeded", "canceled"
            "amount": data.get("amount", {}).get("value")
        }
    else:
        raise Exception(f"Ошибка при проверке статуса: {response.status_code}")