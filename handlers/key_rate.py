# Обработчик кнопки «Ключевая ставка ЦБ РФ».
# Показывает текущую ставку, ближайшее заседание и (если окно открыто) блок прогноза.

import asyncio

from aiogram import Router
from aiogram.types import Message

from keyboards.inline import get_key_rate_keyboard
from services.key_rate_service import get_key_rate_text
from services.forecast_service import (
    get_next_meeting,
    _check_window_open,
    get_user_forecast,
    is_user_subscribed,
    get_user_forecast_history,
)
from utils.constants import MONTHS_RU

router = Router()


@router.message(lambda message: message.text == "Ключевая ставка ЦБ РФ")
async def key_rate_handler(message: Message) -> None:
    """
    Умный обработчик «Ключевая ставка ЦБ РФ».
    Параллельно запрашивает ставку и следующее заседание,
    затем (если окно прогноза открыто) — ещё три запроса параллельно.
    """
    try:
        rate_text, next_meeting = await asyncio.gather(
            get_key_rate_text(),
            get_next_meeting(),
        )
    except Exception:
        await message.answer("Не удалось получить ключевую ставку. Попробуй позже.")
        return

    window_open = _check_window_open(next_meeting)

    if next_meeting:
        d = next_meeting.meeting_date
        meeting_str = f"{d.day} {MONTHS_RU[d.month]} {d.year}"
    else:
        meeting_str = "дата уточняется"

    # Окно прогноза закрыто — просто показываем ставку и дату заседания
    if not window_open:
        await message.answer(
            f"🔑 {rate_text}\n\n"
            f"Следующее заседание по ставке состоится <b>{meeting_str}</b>.",
            parse_mode="HTML"
        )
        return

    # Окно открыто — параллельно запрашиваем прогноз, подписку и историю
    user_forecast, subscribed, history = await asyncio.gather(
        get_user_forecast(message.from_user.id, next_meeting.id),
        is_user_subscribed(message.from_user.id),
        get_user_forecast_history(message.from_user.id),
    )

    if user_forecast:
        text = (
            f"🔑 {rate_text}\n\n"
            f"Следующее заседание — <b>{meeting_str}</b>.\n\n"
            f"✅ Ваш прогноз на ближайшее заседание сохранён: "
            f"<b>{user_forecast.forecast_raw.rstrip('%')}%</b>"
        )
    else:
        text = (
            f"🔑 {rate_text}\n\n"
            f"Следующее заседание — <b>{meeting_str}</b>.\n\n"
            f"Хотите сделать прогноз по следующему решению?"
        )

    keyboard = get_key_rate_keyboard(
        has_forecast=user_forecast is not None,
        is_subscribed=subscribed,
        has_history=len(history) > 0
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
