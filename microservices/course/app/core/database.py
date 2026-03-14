import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger("app.core.database")


# Базовый класс моделей
class Base(DeclarativeBase):
    pass


engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    global engine, async_session_factory
    if engine is not None:
        return
    # Создаём движок SQLAlchemy
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQL_DEBUG)
    # Фабрика сессий
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    logger.debug("Database engine initialized")


async def dispose_engine() -> None:
    global engine, async_session_factory
    if engine is None:
        return
    await engine.dispose()
    engine = None
    async_session_factory = None
    logger.debug("Database engine disposed")


# Dependency для получения сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        raise RuntimeError("Database engine is not initialized")
    async with async_session_factory() as session:
        yield session


# Гарантируем, что все модели будут импортированы и промаппированы
# до того, как кто-то запросит metadata или создаст миграции
import app.models  # noqa: F401
