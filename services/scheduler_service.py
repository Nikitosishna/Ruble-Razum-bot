# Планировщик задач бота.
# Задача 1 (10:00 МСК): напоминания подписчикам без прогноза за 1-2 дня до заседания.
# Задача 2 (13:30 МСК): в день заседания — получить ставку из ЦБ, разослать итоги.

from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.forecast_service import (
    get_next_meeting,
    get_all_subscribers,
    get_user_forecast,
    get_meetings_pending_results,
    get_all_forecasts_for_meeting,
    set_meeting_actual_rate,
    mark_forecast_correct,
    get_user_stats,
)
from services.key_rate_service import fetch_key_rate, invalidate_rate_cache
from utils.constants import MONTHS_RU
from utils.formatters import format_rate_html

MSK = timezone(timedelta(hours=3))


def _parse_rate_str(rate_str: str) -> float:
    """Преобразует строку ЦБ вида '21,0' или '21.0' в float."""
    return float(rate_str.replace(",", ".").replace("%", "").strip())



async def send_forecast_reminders(bot: Bot) -> None:
    """
    Задача 1 — ежедневно в 10:00 МСК.
    Отправляет напоминание подписчикам, у которых ещё нет прогноза
    на ближайшее заседание (за 1 или 2 дня до него).
    """
    meeting = await get_next_meeting()
    if not meeting:
        return

    now_msk = datetime.now(tz=MSK)
    meeting_date_msk = datetime(
        meeting.meeting_date.year,
        meeting.meeting_date.month,
        meeting.meeting_date.day,
        tzinfo=MSK
    )
    days_left = (meeting_date_msk.date() - now_msk.date()).days

    if days_left not in (1, 2):
        return

    meeting_str = f"{meeting.meeting_date.day} {MONTHS_RU[meeting.meeting_date.month]}"
    days_word = "2 дня" if days_left == 2 else "1 день"

    subscribers = await get_all_subscribers()
    if not subscribers:
        return

    sent = 0
    for user_id in subscribers:
        try:
            user_forecast = await get_user_forecast(user_id, meeting.id)
            if user_forecast:
                continue  # уже проголосовал — напоминание не нужно

            text = (
                f"⏰ Напоминание: через {days_word} заседание ЦБ РФ "
                f"(<b>{meeting_str}</b>).\n\n"
                f"Вы ещё не сделали прогноз — успейте до начала заседания!"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🎯 Сделать прогноз", callback_data="make_forecast")
            ]])

            await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            sent += 1

        except Exception as e:
            print(f"[Scheduler] Не удалось отправить напоминание {user_id}: {repr(e)}")

    print(f"[Scheduler] Напоминания отправлены {sent} пользователям (до заседания {days_word})")


async def send_meeting_results(bot: Bot) -> None:
    """
    Задача 2 — ежедневно в 13:30 МСК.
    Проверяет, есть ли прошедшие заседания без разосланных результатов.
    Если да — берёт актуальную ставку из ЦБ, сравнивает с прогнозами, рассылает итоги.
    """
    pending = await get_meetings_pending_results()
    if not pending:
        return

    for meeting in pending:
        try:
            rate_str = await fetch_key_rate()
            actual_rate = _parse_rate_str(rate_str)
        except Exception as e:
            print(f"[Scheduler] Не удалось получить ставку для заседания {meeting.id}: {repr(e)}")
            continue

        await set_meeting_actual_rate(meeting.id, actual_rate)
        await invalidate_rate_cache()  # сбрасываем кэш — ставка изменилась
        rate_display = format_rate_html(actual_rate)

        forecasts = await get_all_forecasts_for_meeting(meeting.id)
        if not forecasts:
            print(f"[Scheduler] Заседание {meeting.id}: прогнозов не было, итоги не рассылаем")
            continue

        print(f"[Scheduler] Рассылаем итоги заседания {meeting.id} → {actual_rate}% ({len(forecasts)} прогнозов)")

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
                await bot.send_message(
                    chat_id=forecast.telegram_user_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"[Scheduler] Не удалось отправить итог {forecast.telegram_user_id}: {repr(e)}")


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Создаёт и запускает планировщик. Вызывается один раз из main.py.
    """
    scheduler = AsyncIOScheduler(timezone=MSK)

    scheduler.add_job(
        send_forecast_reminders,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot],
        name="forecast_reminders"
    )

    scheduler.add_job(
        send_meeting_results,
        trigger="cron",
        hour=13,
        minute=30,
        args=[bot],
        name="meeting_results"
    )

    scheduler.start()
    print("[Scheduler] Планировщик запущен (напоминания: 10:00, итоги: 13:30 МСК)")
    return scheduler
