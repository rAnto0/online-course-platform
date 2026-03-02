from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from collections.abc import AsyncGenerator
from .config import settings


# Базовый класс моделей
class Base(DeclarativeBase):
    pass


# Создаём движок SQLAlchemy
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Фабрика сессий
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


# Dependency для получения сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# Гарантируем, что все модели будут импортированы и промаппированы
# до того, как кто-то запросит metadata или создаст миграции
import app.models  # noqa: F401
