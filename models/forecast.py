# Модели для прогнозов по ключевой ставке ЦБ РФ.

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class CBRMeeting(Base):
    """
    Заседание ЦБ РФ по ключевой ставке.
    """
    __tablename__ = "cbr_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Дата заседания
    meeting_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True)

    # Фактическая ставка — заполняется после решения ЦБ (до этого None)
    actual_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Когда отправили итоги пользователям — чтобы не отправить дважды
    result_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RateForecast(Base):
    """
    Прогноз пользователя на заседание ЦБ.
    Хранится только последний вариант — при изменении запись обновляется.
    """
    __tablename__ = "rate_forecasts"

    __table_args__ = (
        # Гарантирует: 1 запись на пользователя на заседание
        UniqueConstraint("telegram_user_id", "meeting_id", name="uq_user_meeting"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    meeting_id: Mapped[int] = mapped_column(Integer, ForeignKey("cbr_meetings.id"), nullable=False)

    # Прогноз как написал пользователь ("14,5%")
    forecast_raw: Mapped[str] = mapped_column(String(20), nullable=False)

    # Нормализованное число (14.5)
    forecast_value: Mapped[float] = mapped_column(Float, nullable=False)

    # Совпал ли прогноз с решением ЦБ (None — пока решения нет)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Дата последнего прогноза (обновляется при изменении)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RateSubscription(Base):
    """
    Подписка пользователя на напоминания о прогнозах.
    """
    __tablename__ = "rate_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)

    subscribed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)