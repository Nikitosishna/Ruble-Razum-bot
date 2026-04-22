# Обработчики прогнозов ключевой ставки.
# Ввод прогноза, изменение, подписка на напоминания, статистика.

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from services.forecast_service import (
    is_forecast_window_open,
    get_next_meeting,
    get_user_forecast,
    save_forecast,
    normalize_forecast,
    is_user_subscribed,
    subscribe_user,
)
from states.registration import ForecastState

router = Router()


@router.callback_query(lambda c: c.data in ("make_forecast", "change_forecast"))
async def start_forecast_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Запускает сценарий ввода прогноза.
    Работает и для новых прогнозов, и для изменения существующего.
    """
    if not await is_forecast_window_open():
        await callback.message.answer("⏰ Приём прогнозов на это заседание уже завершён.")
        await callback.answer()
        return

    await callback.message.answer(
        "Какую ключевую ставку установит Банк России по итогам ближайшего заседания?\n\n"
        "Отправьте ответ в формате:\n"
        "<code>4</code> / <code>4,5</code> / <code>4.5</code> / <code>4%</code>",
        parse_mode="HTML"
    )
    await state.set_state(ForecastState.waiting_for_forecast)
    await callback.answer()


@router.message(ForecastState.waiting_for_forecast)
async def process_forecast(message: Message, state: FSMContext) -> None:
    """Принимает прогноз пользователя, валидирует и сохраняет."""
    if not await is_forecast_window_open():
        await message.answer("⏰ Приём прогнозов на это заседание уже завершён.")
        await state.clear()
        return

    raw = message.text.strip()
    value = normalize_forecast(raw)

    if value is None:
        await message.answer(
            "❌ Не удалось распознать ответ.\n\n"
            "Отправьте в формате: <code>14</code>, <code>14.5</code>, "
            "<code>14,5</code> или <code>14%</code>",
            parse_mode="HTML"
        )
        return

    next_meeting = await get_next_meeting()
    if not next_meeting:
        await message.answer("⏰ Заседание не найдено. Попробуй позже.")
        await state.clear()
        return

    await save_forecast(
        telegram_user_id=message.from_user.id,
        meeting_id=next_meeting.id,
        forecast_raw=raw,
        forecast_value=value
    )

    subscribed = await is_user_subscribed(message.from_user.id)

    # Кнопки после сохранения прогноза
    buttons = []
    if not subscribed:
        buttons.append([InlineKeyboardButton(
            text="Напомнить о следующим заседании",
            callback_data="subscribe_forecast"
        )])
    buttons.append([
        InlineKeyboardButton(text="Изменить прогноз", callback_data="change_forecast")
    ])

    await message.answer(
        f"✅ Ваш прогноз принят: <b>{raw.rstrip('%')}%</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(lambda c: c.data == "subscribe_forecast")
async def subscribe_forecast_callback(callback: CallbackQuery) -> None:
    """Подписывает пользователя на напоминания о прогнозах."""
    already = await is_user_subscribed(callback.from_user.id)
    if already:
        await callback.message.answer("Вы уже включили напоминание!")
    else:
        await subscribe_user(callback.from_user.id)
        await callback.message.answer(
            "Напоминание о прогнозе перед следующим заседанием включено."
        )
    await callback.answer()


