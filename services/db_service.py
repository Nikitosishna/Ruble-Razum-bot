# Подключение к PostgreSQL и функции для работы с таблицам
# Функции для работы с таблицами users и payments.

from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, select
from sqlalchemy.orm import Mapped, mapped_column

from database import Base, SessionLocal, engine
from models.payment import Payment # нужно, чтобы SQLAlchemy "увидела" таблицу payments
from models.forecast import CBRMeeting, RateForecast, RateSubscription


class User(Base):
    """Модель таблицы users."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db() -> None:
    """Создаёт таблицы в БД, если их ещё нет."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_user(telegram_user_id: int, user_name: str, email: str) -> User:
    """Создаёт нового пользователя в таблице users."""
    async with SessionLocal() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            user_name=user_name,
            email=email
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_by_telegram_id(telegram_user_id: int) -> User | None:
    """Ищет пользователя по telegram_user_id."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()


async def create_payment_record(
    telegram_user_id: int,
    product_name: str,
    amount: float,
    payment_id: str | None = None,
    status: str = "pending"
) -> Payment:
    """
    Создаёт запись о платеже в БД.
    Используется при нажатии "Перейти к оплате".
    """
    async with SessionLocal() as session:
        payment = Payment(
            telegram_user_id=telegram_user_id,
            product_name=product_name,
            amount=amount,
            payment_id=payment_id,
            status=status,
            is_delivered=False
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment


async def get_payment_by_payment_id(payment_id: str) -> Payment | None:
    """Ищет платёж по payment_id из ЮKassa. Пригодится для webhook-логики."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()


async def get_succeeded_guide_payment(telegram_user_id: int) -> Payment | None:
    """
    Проверяет, есть ли у пользователя успешно оплаченный гайд.
    Используется перед созданием нового платежа чтобы не брать деньги повторно.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.telegram_user_id == telegram_user_id,
                Payment.product_name == "guide_financial_literacy",
                Payment.status == "succeeded"
            ).limit(1)
        )
        return result.scalar_one_or_none()


async def update_payment_status(payment_id: str, status: str) -> None:
    """
    Обновляет статус платежа в БД.
    Используется webhook-обработчиком после успешной оплаты.
    Защищает от повторной отправки гайда при дублирующихся уведомлениях.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = status
            await session.commit()
