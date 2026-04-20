# Базовый класс для всех моделей БД + движок и фабрика сессий.
# Вынесено в отдельный файл, чтобы модели (User, Payment) могли импортировать Base,
# не завися друг от друга.

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import config


class Base(DeclarativeBase):
    """Базовый класс для ORM-моделей. Все таблицы наследуются от него."""
    pass


engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # переподключается при обрыве соединения (важно для Supabase)
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)