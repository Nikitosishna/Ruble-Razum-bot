# Административные команды — только для ADMIN_ID.
# /update_dates — добавить даты заседаний ЦБ
# /list_dates   — показать все даты из БД
# /set_rate     — вручную сохранить ставку и разослать итоги (резервный сценарий)

from datetime import datetime, timedelta

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from config import config
from database import SessionLocal
from models.forecast import CBRMeeting
from services.forecast_service import (
    update_meeting_dates,
    get_all_meetings,
    get_all_forecasts_for_meeting,
    set_meeting_actual_rate,
    mark_forecast_correct,
    get_user_stats,
)
from services.key_rate_service import invalidate_rate_cache
from utils.constants import MONTHS_RU
from utils.formatters import format_rate_html

router = Router()


@router.message(Command("update_dates"))
async def update_dates_handler(message: Message) -> None:
    """
    Добавляет новые даты заседаний ЦБ в БД.
    Формат: /update_dates 2026-02-13 2026-03-20 2026-04-24
    """
    if message.from_user.id != config.ADMIN_ID:
        return  # Молча игнорируем — обычные пользователи не знают об этой команде

    args = message.text.strip().split()[1:]
    if not args:
        await message.answer(
            "⚠️ Укажи даты через пробел.\n\n"
            "Пример: <code>/update_dates 2026-02-13 2026-03-20</code>",
            parse_mode="HTML"
        )
        return

    parsed = []
    errors = []
    for raw_date in args:
        try:
            parsed.append(datetime.strptime(raw_date.strip(), "%Y-%m-%d"))
        except ValueError:
            errors.append(raw_date)

    if errors:
        await message.answer(
            f"❌ Не удалось распознать даты: {', '.join(errors)}\n\n"
            "Используй формат <code>ГГГГ-ММ-ДД</code>, например <code>2026-02-13</code>",
            parse_mode="HTML"
        )
        return

    added = await update_meeting_dates(parsed)
    await message.answer(
        f"✅ Готово! Добавлено новых дат: <b>{added}</b> из {len(parsed)}.\n"
        "Уже существующие даты пропущены.",
        parse_mode="HTML"
    )


@router.message(Command("list_dates"))
async def list_dates_handler(message: Message) -> None:
    """
    Показывает все даты заседаний ЦБ из БД.
    Прошедшие — ✅, будущие — 🕐.
    """
    if message.from_user.id != config.ADMIN_ID:
        return

    meetings = await get_all_meetings()
    if not meetings:
        await message.answer("📭 В базе данных нет ни одной даты заседания.")
        return

    now = datetime.utcnow()
    lines = []
    current_year = None

    for m in meetings:
        d = m.meeting_date
        if d.year != current_year:
            current_year = d.year
            lines.append(f"\n<b>— {d.year} —</b>")
        icon = "✅" if d < now else "🕐"
        lines.append(f"{icon} {d.day} {MONTHS_RU[d.month]}")

    text = f"<b>Все даты заседаний ЦБ в базе ({len(meetings)} шт.):</b>\n" + "\n".join(lines)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("set_rate"))
async def set_rate_handler(message: Message) -> None:
    """
    Резервная команда для ручной рассылки итогов заседания ЦБ.
    Используется если автоматическая рассылка в 13:30 не сработала.

    Формат: /set_rate 2026-04-24 21.0
    Находит заседание по дате (±1 день), сохраняет ставку и рассылает итоги.
    """
    if message.from_user.id != config.ADMIN_ID:
        return

    args = message.text.strip().split()[1:]
    if len(args) != 2:
        await message.answer(
            "⚠️ Формат: <code>/set_rate 2026-04-24 21.0</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_date = datetime.strptime(args[0].strip(), "%Y-%m-%d")
        actual_rate = float(args[1].strip().replace(",", "."))
    except ValueError:
        await message.answer(
            "❌ Не удалось распознать дату или ставку.\n"
            "Формат: <code>/set_rate 2026-04-24 21.0</code>",
            parse_mode="HTML"
        )
        return

    # Ищем заседание по дате ±1 день
    window_start = target_date - timedelta(days=1)
    window_end = target_date + timedelta(days=1)

    async with SessionLocal() as session:
        result = await session.execute(
            select(CBRMeeting).where(
                CBRMeeting.meeting_date >= window_start,
                CBRMeeting.meeting_date <= window_end,
            ).limit(1)
        )
        meeting = result.scalar_one_or_none()

    if not meeting:
        await message.answer(
            f"❌ Заседание на дату <b>{args[0]}</b> не найдено в БД.\n"
            "Проверь дату или добавь через /update_dates.",
            parse_mode="HTML"
        )
        return

    if meeting.result_sent_at:
        await message.answer(
            f"⚠️ Итоги по этому заседанию уже были разосланы "
            f"({meeting.result_sent_at.strftime('%d.%m.%Y %H:%M')} UTC)."
        )
        return

    await set_meeting_actual_rate(meeting.id, actual_rate)
    await invalidate_rate_cache()
    rate_display = format_rate_html(actual_rate)

    forecasts = await get_all_forecasts_for_meeting(meeting.id)
    if not forecasts:
        await message.answer(
            f"✅ Ставка {rate_display} сохранена. Прогнозов на это заседание не было.",
            parse_mode="HTML"
        )
        return

    sent = 0
    for forecast in forecasts:
        is_correct = round(forecast.forecast_value, 2) == round(actual_rate, 2)
        await mark_forecast_correct(forecast.id, is_correct)
        correct_count, total_count = await get_user_stats(forecast.telegram_user_id)

        if is_correct:
            text = (
                f"🎉 Поздравляю! Ваш ответ совпал с решением Центрального Банка.\n"
                f"Текущая ключевая ставка — {rate_display}.\n\n"
                f"В этом году ваше мнение совпало {correct_count}/{total_count} раз."
            )
        else:
            text = (
                f"📋 В этот раз ваш ответ не совпал с решением Центрального Банка.\n"
                f"Текущая ключевая ставка — {rate_display}.\n\n"
                f"В этом году ваше мнение совпало {correct_count}/{total_count} раз."
            )

        try:
            await message.bot.send_message(
                chat_id=forecast.telegram_user_id,
                text=text,
                parse_mode="HTML"
            )
            sent += 1
        except Exception as e:
            print(f"[set_rate] Не удалось отправить итог {forecast.telegram_user_id}: {repr(e)}")

    await message.answer(
        f"✅ Готово! Ставка {rate_display} сохранена.\n"
        f"Итоги разосланы {sent} из {len(forecasts)} участников.",
        parse_mode="HTML"
    )
