# Обработчики сообщений и кнопок.

from aiogram import Router
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, desc

from services.file_service import (
    get_privacy_policy_file,
    get_offer_file,
    get_guide_file,
    get_community_image_file,
    get_what_can_bot_image_file,
)
from keyboards.reply import get_main_keyboard
from keyboards.inline import (
    get_community_inline_keyboard,
    get_currency_inline_keyboard,
    get_guide_payment_inline_keyboard,
    get_documents_inline_keyboard,
    get_key_rate_keyboard,
)
from utils.validators import is_valid_name, is_valid_email
from utils.constants import MONTHS_RU
from services.db_service import create_user, get_user_by_telegram_id, create_payment_record, get_succeeded_guide_payment
from services.payment_service import create_payment, get_payment_status
from services.currency_service import get_fiat_rate, get_crypto_rate
from services.key_rate_service import get_key_rate_text
from services.forecast_service import (
    get_next_meeting,
    get_all_meetings,
    is_forecast_window_open,
    _check_window_open,
    get_user_forecast,
    save_forecast,
    normalize_forecast,
    is_user_subscribed,
    subscribe_user,
    update_meeting_dates,
    get_all_forecasts_for_meeting,
    set_meeting_actual_rate,
    mark_forecast_correct,
    get_user_stats,
    get_user_forecast_history,
)
from states.registration import RegistrationState, ForecastState
from config import config

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.
    Логика:
    1. Если пользователь уже зарегистрирован — сразу показываем главное меню.
    2. Если пользователь новый — сразу начинаем регистрацию.
    """

    await state.clear()

    telegram_user_id = message.from_user.id
    existing_user = await get_user_by_telegram_id(telegram_user_id)

    if existing_user:
        await message.answer(
            text=(
                f"С возвращением, {existing_user.user_name}!\n"
                "Бот «Рубль Разум» готов к работе."
            ),
            reply_markup=get_main_keyboard()
        )
        return

    await message.answer(
        text="Пожалуйста, введи своё имя."
    )
    await state.set_state(RegistrationState.waiting_for_name)


@router.message(RegistrationState.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    """
    Обработчик ввода имени.
    """

    name = message.text.strip()

    if not is_valid_name(name):
        await message.answer(
            "Имя введено некорректно.\nПожалуйста, попробуй ещё раз."
        )
        return

    await state.update_data(user_name=name)

    await message.answer(
        text=f"Привет, {name}!\nТеперь введи свою электронную почту."
    )

    await state.set_state(RegistrationState.waiting_for_email)


@router.message(RegistrationState.waiting_for_email)
async def process_email(message: Message, state: FSMContext) -> None:
    """
    Обработчик ввода email.
    """

    email = message.text.strip().lower()

    if not is_valid_email(email):
        await message.answer("Пожалуйста, введи корректную почту.")
        return

    data = await state.get_data()
    user_name = data["user_name"]

    await create_user(
        telegram_user_id=message.from_user.id,
        user_name=user_name,
        email=email
    )

    await message.answer(
        text=(
            "Добро пожаловать в бот сообщества «Рубль Разум»!\n\n"
            "Здесь можно:\n"
            "• Приобрести гайд по финансовой грамотности;\n"
            "• Посмотреть актуальные курсы валют;\n"
            "• Узнать стоимость BTC и ETH;\n"
            "• Узнать текущую ключевую ставку ЦБ РФ;\n"
            "• Поучаствовать в прогнозах ключевой ставки.\n\n"
            "Что вас интересует?"
        ),
        reply_markup=get_main_keyboard()
    )

    await state.clear()


@router.message(lambda message: message.text == "Что умеет бот?")
async def what_can_bot_handler(message: Message) -> None:
    """
    Обработчик кнопки 'Что умеет бот?'.
    Отправляет краткое описание возможностей бота + изображение.
    """

    try:
        what_can_bot_image = get_what_can_bot_image_file()

        await message.answer_photo(
            photo=what_can_bot_image,
            caption=(
                "Это бот сообщества «Рубль Разум»!\n\n"
                "Здесь можно:\n"
                "• Приобрести гайд по финансовой грамотности;\n"
                "• Посмотреть актуальные курсы валют;\n"
                "• Узнать стоимость BTC и ETH;\n"
                "• Узнать текущую ключевую ставку ЦБ РФ;\n"
                "• Поучаствовать в прогнозах ключевой ставки.\n\n"
                "Что вас интересует?"
            )
        )
    except Exception as e:
        await message.answer(
            text=f"Не удалось отправить изображение: {e}"
        )


@router.message(lambda message: message.text == "Сообщество")
async def community_handler(message: Message) -> None:
    """
    Обработчик кнопки 'Сообщество'.
    Отправляет картинку сообщества с подписью и кнопкой-ссылкой.
    """

    try:
        community_image = get_community_image_file()

        await message.answer_photo(
            photo=community_image,
            caption="Нажми на кнопку, чтобы перейти в сообщество.",
            reply_markup=get_community_inline_keyboard()
        )
    except Exception as e:
        await message.answer(
            text=f"Не удалось отправить изображение сообщества: {e}"
        )


@router.message(lambda message: message.text == "Купить гайд")
async def guide_handler(message: Message) -> None:
    """
    Обработчик кнопки 'Купить гайд'.
    Отправляет два сообщения:
    1. Краткое описание и аудитория гайда
    2. Содержание, цена и кнопка перехода к оплате
    """

    guide_text = (
        "<b>📚 Гайд по финансовой грамотности</b>\n\n"
        "Практический гайд по финансовой грамотности, который поможет разобраться "
        "в личных финансах, навести в них порядок и заложить понятную базу для "
        "накоплений, целей и первых инвестиций.\n\n"
        "Гайд будет полезен тем, кто хочет:\n"
        "🎯 Понять своё текущее финансовое положение;\n"
        "🎯 Выстроить финансовые цели;\n"
        "🎯 Сформировать полезные привычки;\n"
        "🎯 Спокойнее относиться к накоплениям, кредитам и инвестициям.\n\n"
        "Внутри раскрыты следующие темы:\n"
        "1. Что такое финансовая грамотность\n"
        "2. Как устроены отношения с деньгами\n"
        "3. Как оценить своё финансовое состояние\n"
        "4. Как поставить финансовые цели\n"
        "5. Какие привычки помогают управлять деньгами\n"
        "6. Как работают вклады, накопительные счета и кредиты\n"
        "7. Что важно знать перед началом инвестирования\n"
        "8. Чем отличаются облигации и акции\n"
        "9. Как выстроить финансовый план на несколько лет вперёд\n\n"
        "🌐 Бонусный раздел по криптовалютам: основы крипты и блокчейна,"
        " базовые виды активов, кошельки, риски и принципы безопасности\n\n"
        "💰 Стоимость: <s>1490 ₽</s> <b>1099 ₽</b>\n\n"
        "Без лишней теории и громких обещаний — база, которая поможет лучше понимать,"
        " как работают финансовые инструменты."
    )

    await message.answer(
        text=guide_text,
        reply_markup=get_guide_payment_inline_keyboard(),
        parse_mode="HTML"
    )

    await message.answer(
        text="📄✍🏼 Переходя к оплате, вы соглашаетесь с офертой и политикой конфиденциальности.",
        reply_markup=get_documents_inline_keyboard()
    )


@router.message(lambda message: message.text == "Актуальные курсы валют")
async def currency_handler(message: Message) -> None:
    """
    Обработчик кнопки 'Актуальные курсы валют'.
    Показывает inline-кнопки выбора валюты.
    """

    await message.answer(
        text="Выбери валюту, чтобы узнать актуальный курс:",
        reply_markup=get_currency_inline_keyboard()
    )


@router.message(lambda message: message.text == "Ключевая ставка ЦБ РФ")
async def key_rate_handler(message: Message) -> None:
    """
    Умный обработчик кнопки 'Ключевая ставка ЦБ РФ'.
    Показывает разный текст и кнопки в зависимости от ситуации.
    """
    import asyncio as _asyncio

    # Параллельно запрашиваем ставку ЦБ и следующее заседание
    try:
        rate_text, next_meeting = await _asyncio.gather(
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

    if not window_open:
        await message.answer(
            f"🔑 {rate_text}\n\n"
            f"Следующее заседание по ставке состоится <b>{meeting_str}</b>.",
            parse_mode="HTML"
        )
        return

    # Окно открыто — параллельно запрашиваем прогноз, подписку и историю
    user_forecast, subscribed, history = await _asyncio.gather(
        get_user_forecast(message.from_user.id, next_meeting.id),
        is_user_subscribed(message.from_user.id),
        get_user_forecast_history(message.from_user.id),
    )

    if user_forecast:
        text = (
            f"🔑 {rate_text}\n\n"
            f"Следующее заседание — <b>{meeting_str}</b>.\n\n"
            f"✅ Ваш прогноз на ближайшее заседание сохранён: "
            f"<b>{user_forecast.forecast_raw}</b>"
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


# Универсальные обработчики курса валют

FIAT_CURRENCY_MAP = {
    "currency_usd": "USD",
    "currency_eur": "EUR",
    "currency_cny": "CNY",
    "currency_aed": "AED",
    "currency_try": "TRY",
    "currency_gbp": "GBP",
    "currency_gel": "GEL",
    "currency_byn": "BYN",
    "currency_kzt": "KZT",
    "currency_chf": "CHF",
}

CRYPTO_CURRENCY_MAP = {
    "currency_btc": "BTC",
    "currency_eth": "ETH",
}


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


@router.callback_query(lambda callback: callback.data == "buy_guide")
async def buy_guide_callback(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки 'Перейти к оплате'.
    Создаёт платёж в ЮKassa и отправляет ссылку на оплату.
    """
    await callback.answer()  # Сразу убираем «загрузку» у кнопки

    # Проверяем, не покупал ли пользователь гайд ранее
    existing = await get_succeeded_guide_payment(callback.from_user.id)
    if existing:
        await callback.message.answer(
            "📚 Вы уже приобретали этот гайд ранее. Отправляю его повторно!"
        )
        guide_file = get_guide_file()
        await callback.message.answer_document(guide_file)
        return

    try:
        payment_data = await create_payment(
            amount=1099.00,
            description="Гайд по финансовой грамотности"
        )

        await create_payment_record(
            telegram_user_id=callback.from_user.id,
            product_name="guide_financial_literacy",
            amount=1099.00,
            payment_id=payment_data["payment_id"],
            status=payment_data["status"]
        )

        confirmation_url = payment_data.get("confirmation_url")
        if confirmation_url:
            await callback.message.answer(
                text=(
                    "✅ <b>Платёж создан!</b>\n\n"
                    f"🔗 <a href='{confirmation_url}'>Перейти к оплате</a>\n\n"
                    "После оплаты гайд придёт в этот чат автоматически."
                ),
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("❌ Ошибка при создании платежа")

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda callback: callback.data == "open_privacy_policy")
async def open_privacy_policy_callback(callback: CallbackQuery) -> None:
    """
    Отправляет PDF политики конфиденциальности.
    """

    try:
        privacy_file = get_privacy_policy_file()
        await callback.message.answer_document(privacy_file)
        await callback.answer()
    except Exception as e:
        print("Ошибка при отправке политики конфиденциальности:", repr(e))
        await callback.answer("Не удалось отправить файл", show_alert=True)


@router.callback_query(lambda callback: callback.data == "open_offer")
async def open_offer_callback(callback: CallbackQuery) -> None:
    """
    Отправляет PDF оферты.
    """

    try:
        offer_file = get_offer_file()
        await callback.message.answer_document(offer_file)
        await callback.answer()
    except Exception as e:
        print("Ошибка при отправке оферты:", repr(e))
        await callback.answer("Не удалось отправить файл", show_alert=True)


@router.callback_query(lambda callback: callback.data == "check_payment_status")
async def check_payment_status_callback(callback: CallbackQuery) -> None:
    """
    Проверяет статус последнего платежа пользователя.
    Если оплачен — отправляет PDF гайда.
    """
    try:
        from models.payment import Payment
        from database import SessionLocal

        # Ищем последний платёж этого пользователя в БД
        async with SessionLocal() as session:
            result = await session.execute(
                select(Payment)
                .where(Payment.telegram_user_id == callback.from_user.id)
                .order_by(desc(Payment.id))
                .limit(1)
            )
            payment = result.scalar_one_or_none()

        if not payment or not payment.payment_id:
            await callback.message.answer(
                "❌ Платёж не найден. Сначала нажми «Перейти к оплате»."
            )
            await callback.answer()
            return

        # Проверяем статус в ЮKassa
        payment_info = await get_payment_status(payment.payment_id)
        status = payment_info.get("status")

        if status == "succeeded":
            await callback.message.answer(
                "💳 Оплата прошла успешно! Отправляю гайд.\n\n"
                "Поздравляю — вы сделали первый шаг к более осознанному управлению своими финансами."

            )
            guide_file = get_guide_file()
            await callback.message.answer_document(guide_file)

        elif status == "pending":
            await callback.message.answer(
                "⏳ Оплата ещё не прошла. Оплати по ссылке выше и попробуй снова."
            )

        elif status == "canceled":
            await callback.message.answer(
                "❌ Платёж отменён. Нажми «Перейти к оплате» ещё раз."
            )

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


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
        "Отправьте ответ в формате: <code>5</code>, <code>5.5</code>, "
        "<code>5,5</code> или <code>5%</code>",
        parse_mode="HTML"
    )
    await state.set_state(ForecastState.waiting_for_forecast)
    await callback.answer()


@router.message(ForecastState.waiting_for_forecast)
async def process_forecast(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает введённый пользователем прогноз.
    """
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

    buttons = []
    if not subscribed:
        buttons.append([InlineKeyboardButton(
            text="🔔 Напомнить перед следующим заседанием",
            callback_data="subscribe_forecast"
        )])
    buttons.append([
        InlineKeyboardButton(text="🖍️ Изменить прогноз", callback_data="change_forecast")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"✅ Ваш прогноз принят: <b>{raw}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.clear()


@router.message(Command("update_dates"))
async def update_dates_handler(message: Message) -> None:
    """
    Команда /update_dates — только для администратора.
    Добавляет новые даты заседаний в БД.

    Формат: /update_dates 2026-02-13 2026-03-20 2026-04-24
    """
    if message.from_user.id != config.ADMIN_ID:
        return  # Молча игнорируем — обычные пользователи не знают об этой команде

    args = message.text.strip().split()[1:]  # Убираем саму команду /update_dates
    if not args:
        await message.answer(
            "⚠️ Укажи даты через пробел.\n\n"
            "Пример: <code>/update_dates 2026-02-13 2026-03-20</code>",
            parse_mode="HTML"
        )
        return

    from datetime import datetime  # noqa: PLC0415
    parsed = []
    errors = []

    for raw_date in args:
        try:
            dt = datetime.strptime(raw_date.strip(), "%Y-%m-%d")
            parsed.append(dt)
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
        f"Уже существующие даты пропущены.",
        parse_mode="HTML"
    )


@router.message(Command("list_dates"))
async def list_dates_handler(message: Message) -> None:
    """
    Команда /list_dates — только для администратора.
    Показывает все даты заседаний ЦБ, сохранённые в БД.
    Прошедшие даты помечаются галочкой, будущие — часами.
    """
    if message.from_user.id != config.ADMIN_ID:
        return

    from datetime import datetime  # noqa: PLC0415
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

    text = f"📅 <b>Все даты заседаний ЦБ в базе ({len(meetings)} шт.):</b>\n" + "\n".join(lines)
    await message.answer(text, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "subscribe_forecast")
async def subscribe_forecast_callback(callback: CallbackQuery) -> None:
    """
    Подписывает пользователя на напоминания о прогнозах.
    """
    already = await is_user_subscribed(callback.from_user.id)
    if already:
        await callback.message.answer("Вы уже включили напоминание!")
    else:
        await subscribe_user(callback.from_user.id)
        await callback.message.answer(
            "Напоминание о прогнозе перед следующим заседанием включено."
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "my_stats")
async def my_stats_callback(callback: CallbackQuery) -> None:
    """
    Показывает пользователю его статистику прогнозов за текущий год.
    """
    history = await get_user_forecast_history(callback.from_user.id)
    correct_count, total_count = await get_user_stats(callback.from_user.id)

    if not history:
        await callback.message.answer("У вас пока нет завершённых прогнозов за этот год.")
        await callback.answer()
        return

    lines = []
    for entry in history:
        d = entry["date"]
        date_str = f"{d.day} {MONTHS_RU[d.month]}"
        icon = "✅" if entry["is_correct"] else "❌"
        actual = entry["actual_rate"]
        actual_str = f"{int(actual)}%" if actual == int(actual) else f"{actual:.1f}%".replace(".", ",")
        lines.append(f"{icon} {date_str} — ваш прогноз: <b>{entry['forecast_raw']}</b>, решение: <b>{actual_str}</b>")

    text = (
        f"📊 <b>Ваша статистика за {history[0]['date'].year} год</b>\n\n"
        + "\n".join(lines)
        + f"\n\n<b>Итог: {correct_count}/{total_count} верных прогнозов</b>"
    )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(Command("set_rate"))
async def set_rate_handler(message: Message) -> None:
    """
    Команда /set_rate — только для администратора. Fallback на случай,
    если автоматическая рассылка в 13:30 не сработала.

    Формат: /set_rate 2026-04-24 21.0
    Находит заседание по дате (±1 день), сохраняет ставку и рассылает итоги.
    """
    if message.from_user.id != config.ADMIN_ID:
        return

    from datetime import datetime, timedelta  # noqa: PLC0415
    from services.scheduler_service import _format_rate  # noqa: PLC0415

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
    from models.forecast import CBRMeeting  # noqa: PLC0415
    from database import SessionLocal  # noqa: PLC0415

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
    rate_display = _format_rate(actual_rate)

    forecasts = await get_all_forecasts_for_meeting(meeting.id)
    if not forecasts:
        await message.answer(
            f"✅ Ставка {rate_display} сохранена. Прогнозов на это заседание не было."
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
            await message.bot.send_message(chat_id=forecast.telegram_user_id, text=text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            print(f"[set_rate] Не удалось отправить итог {forecast.telegram_user_id}: {repr(e)}")

    await message.answer(
        f"✅ Готово! Ставка {rate_display} сохранена.\n"
        f"Итоги разосланы {sent} из {len(forecasts)} участников.",
        parse_mode="HTML"
    )