# Создание БД с оплатами и инфой по ним

from sqlalchemy import BigInteger, Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Payment(Base):
    """
    Модель платежа.
    Хранит информацию о попытках оплаты и их статусах.
    В будущем будет использоваться для интеграции с ЮKassa.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
    )

    is_delivered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )