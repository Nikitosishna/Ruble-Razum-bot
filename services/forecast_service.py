# Сервис для прогнозов по ключевой ставке ЦБ РФ.
# Даты заседаний хранятся в БД. При первом запуске заполняются из MEETING_DATES.
# Обновить даты на новый год: команда /update_dates в боте (только для админа).

from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from database import SessionLocal
from models.forecast import CBRMeeting, RateForecast, RateSubscription

# Московское время (UTC+3)
MSK = timezone(timedelta(hours=3))

# Официальный календарь заседаний ЦБ РФ на 2026 год (cbr.ru/dkp/cal_mp/)
# Используется только для первоначального заполнения БД.
# Обновление на следующий год: /update_dates ГГГГ-ММ-ДД ...
MEETING_DATES = [
    datetime(2026, 2, 13, tzinfo=MSK),
    datetime(2026, 3, 20, tzinfo=MSK),
    datetime(2026, 4, 24, tzinfo=MSK),
    datetime(2026, 6, 19, tzinfo=MSK),
    datetime(2026, 7, 24, tzinfo=MSK),
    datetime(2026, 9, 11, tzinfo=MSK),
    datetime(2026, 10, 23, tzinfo=MSK),
    datetime(2026, 12, 18, tzinfo=MSK),
]


async def seed_meeting_dates() -> None:
    """
    При первом запуске записывает MEETING_DATES в таблицу cbr_meetings.
    Если записи уже есть — ничего не делает.
    """
    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(CBRMeeting))
        if count and count > 0:
            return
        for dt in MEETING_DATES:
            session.add(CBRMeeting(meeting_date=dt.replace(tzinfo=None)))
        await session.commit()
        print(f"[CBR] Записано {len(MEETING_DATES)} дат заседаний в БД")


async def update_meeting_dates(dates: list[datetime]) -> int:
    """
    Добавляет новые даты заседаний в БД.
    Уже существующие даты пропускает.
    Возвращает количество добавленных дат.
    """
    added = 0
    async with SessionLocal() as session:
        for dt in dates:
            existing = await session.scalar(
                select(CBRMeeting).where(
                    CBRMeeting.meeting_date == dt.replace(tzinfo=None)
                )
            )
            if not existing:
                session.add(CBRMeeting(meeting_date=dt.replace(tzinfo=None)))
                added += 1
        await session.commit()
    return added


async def get_all_meetings() -> list[CBRMeeting]:
    """
    Возвращает все заседания из БД, отсортированные по дате.
    Используется для отображения списка дат администратору.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(CBRMeeting).order_by(CBRMeeting.meeting_date)
        )
        return list(result.scalars().all())


async def get_next_meeting() -> CBRMeeting | None:
    """
    Возвращает запись ближайшего будущего заседания из БД.
    """
    now_utc = datetime.utcnow()
    async with SessionLocal() as session:
        result = await session.execute(
            select(CBRMeeting)
            .where(CBRMeeting.meeting_date >= now_utc)
            .order_by(CBRMeeting.meeting_date)
            .limit(1)
        )
        return result.scalar_one_or_none()


def _check_window_open(meeting) -> bool:
    """Проверяет окно прогноза по уже загруженному объекту заседания (без запроса в БД)."""
    if not meeting:
        return False
    now = datetime.now(tz=MSK)
    meeting_aware = datetime(
        meeting.meeting_date.year,
        meeting.meeting_date.month,
        meeting.meeting_date.day,
        tzinfo=MSK
    )
    minutes_left = (meeting_aware - now).total_seconds() / 60
    return 30 <= minutes_left <= 2 * 24 * 60


async def is_forecast_window_open() -> bool:
    """
    Окно прогноза открыто если:
    - до заседания 2 дня или меньше
    - до заседания ещё больше 30 минут
    """
    meeting = await get_next_meeting()
    return _check_window_open(meeting)


def normalize_forecast(raw: str) -> float | None:
    """
    Нормализует прогноз пользователя в число.
    Принимает: "14", "14.5", "14,5", "14%", "14,5%"
    Возвращает: 14.5 или None если формат неверный.
    """
    value = raw.strip().replace("%", "").replace(",", ".").strip()
    try:
        result = float(value)
        if 1.0 <= result <= 50.0:
            return result
        return None
    except ValueError:
        return None


async def get_user_forecast(telegram_user_id: int, meeting_id: int) -> RateForecast | None:
    """Возвращает прогноз пользователя на конкретное заседание (или None)."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(RateForecast).where(
                RateForecast.telegram_user_id == telegram_user_id,
                RateForecast.meeting_id == meeting_id
            )
        )
        return result.scalar_one_or_none()


async def save_forecast(
    telegram_user_id: int,
    meeting_id: int,
    forecast_raw: str,
    forecast_value: float
) -> RateForecast:
    """
    Сохраняет или обновляет прогноз пользователя.
    В БД хранится только последний вариант.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(RateForecast).where(
                RateForecast.telegram_user_id == telegram_user_id,
                RateForecast.meeting_id == meeting_id
            )
        )
        forecast = result.scalar_one_or_none()

        if forecast:
            forecast.forecast_raw = forecast_raw
            forecast.forecast_value = forecast_value
            forecast.updated_at = datetime.utcnow()
        else:
            forecast = RateForecast(
                telegram_user_id=telegram_user_id,
                meeting_id=meeting_id,
                forecast_raw=forecast_raw,
                forecast_value=forecast_value
            )
            session.add(forecast)

        await session.commit()
        await session.refresh(forecast)
        return forecast


async def is_user_subscribed(telegram_user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на напоминания."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(RateSubscription).where(
                RateSubscription.telegram_user_id == telegram_user_id
            )
        )
        return result.scalar_one_or_none() is not None


async def subscribe_user(telegram_user_id: int) -> None:
    """Подписывает пользователя на напоминания."""
    async with SessionLocal() as session:
        existing = await session.scalar(
            select(RateSubscription).where(
                RateSubscription.telegram_user_id == telegram_user_id
            )
        )
        if not existing:
            session.add(RateSubscription(telegram_user_id=telegram_user_id))
            await session.commit()


async def get_all_subscribers() -> list[int]:
    """
    Возвращает список telegram_user_id всех подписчиков на напоминания.
    """
    async with SessionLocal() as session:
        result = await session.execute(select(RateSubscription))
        rows = result.scalars().all()
        return [row.telegram_user_id for row in rows]


async def get_meetings_pending_results() -> list[CBRMeeting]:
    """
    Возвращает заседания, которые уже состоялись (дата прошла),
    но actual_rate ещё не заполнен (результаты не разосланы).
    """
    now_utc = datetime.utcnow()
    async with SessionLocal() as session:
        result = await session.execute(
            select(CBRMeeting)
            .where(
                CBRMeeting.meeting_date <= now_utc,
                CBRMeeting.actual_rate.is_(None)
            )
            .order_by(CBRMeeting.meeting_date)
        )
        return list(result.scalars().all())


async def set_meeting_actual_rate(meeting_id: int, actual_rate: float) -> None:
    """
    Сохраняет фактическую ставку по итогам заседания и ставит метку времени рассылки.
    """
    async with SessionLocal() as session:
        meeting = await session.get(CBRMeeting, meeting_id)
        if meeting:
            meeting.actual_rate = actual_rate
            meeting.result_sent_at = datetime.utcnow()
            await session.commit()


async def get_latest_confirmed_rate() -> float | None:
    """
    Возвращает actual_rate последнего состоявшегося заседания ЦБ (или None).
    Используется в key_rate_service для сверки с ответом CBR API после устаревания кэша:
    если CBR ещё не обновился — показываем подтверждённую ставку из БД.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(CBRMeeting.actual_rate)
            .where(CBRMeeting.actual_rate.is_not(None))
            .order_by(CBRMeeting.meeting_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_all_forecasts_for_meeting(meeting_id: int) -> list[RateForecast]:
    """
    Возвращает все прогнозы пользователей на конкретное заседание.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(RateForecast).where(RateForecast.meeting_id == meeting_id)
        )
        return list(result.scalars().all())


async def mark_forecast_correct(forecast_id: int, is_correct: bool) -> None:
    """Обновляет поле is_correct у прогноза."""
    async with SessionLocal() as session:
        forecast = await session.get(RateForecast, forecast_id)
        if forecast:
            forecast.is_correct = is_correct
            await session.commit()


async def get_user_stats(telegram_user_id: int) -> tuple[int, int]:
    """
    Возвращает (угадал, всего) за текущий год.
    Учитываются только прогнозы, у которых is_correct уже заполнен.
    """
    current_year = datetime.utcnow().year
    year_start = datetime(current_year, 1, 1)
    year_end = datetime(current_year, 12, 31, 23, 59, 59)

    async with SessionLocal() as session:
        result = await session.execute(
            select(RateForecast)
            .join(CBRMeeting, RateForecast.meeting_id == CBRMeeting.id)
            .where(
                RateForecast.telegram_user_id == telegram_user_id,
                RateForecast.is_correct.is_not(None),
                CBRMeeting.meeting_date >= year_start,
                CBRMeeting.meeting_date <= year_end,
            )
        )
        forecasts = result.scalars().all()

    total = len(forecasts)
    correct = sum(1 for f in forecasts if f.is_correct)
    return correct, total


async def get_user_forecast_history(telegram_user_id: int) -> list[dict]:
    """
    Возвращает историю прогнозов пользователя за текущий год.
    Каждый элемент: {date, forecast_raw, actual_rate, is_correct}
    Включает только заседания с уже известным результатом.
    """
    current_year = datetime.utcnow().year
    year_start = datetime(current_year, 1, 1)
    year_end = datetime(current_year, 12, 31, 23, 59, 59)

    async with SessionLocal() as session:
        result = await session.execute(
            select(RateForecast, CBRMeeting)
            .join(CBRMeeting, RateForecast.meeting_id == CBRMeeting.id)
            .where(
                RateForecast.telegram_user_id == telegram_user_id,
                RateForecast.is_correct.is_not(None),
                CBRMeeting.meeting_date >= year_start,
                CBRMeeting.meeting_date <= year_end,
            )
            .order_by(CBRMeeting.meeting_date)
        )
        rows = result.all()

    history = []
    for forecast, meeting in rows:
        history.append({
            "date": meeting.meeting_date,
            "forecast_raw": forecast.forecast_raw,
            "actual_rate": meeting.actual_rate,
            "is_correct": forecast.is_correct,
        })
    return history
