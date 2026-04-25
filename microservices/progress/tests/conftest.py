import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_async_session
from app.main import app

pytest_plugins = ("tests.factories",)


@pytest.fixture(scope="session")
def faker():
    import faker

    return faker.Faker()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        settings.DATABASE_TEST_URL, echo=False, poolclass=NullPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    async with async_engine.connect() as conn:
        trans = await conn.begin()
        async_session = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )

        async with async_session() as session:
            await session.begin_nested()

            def _restart_savepoint(session_, transaction):
                if not session_.in_nested_transaction():
                    session_.begin_nested()

            event.listen(
                session.sync_session, "after_transaction_end", _restart_savepoint
            )

            try:
                yield session
            finally:
                event.remove(
                    session.sync_session, "after_transaction_end", _restart_savepoint
                )
                await session.close()
                await trans.rollback()


@pytest_asyncio.fixture
async def override_get_db(db_session):
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest_asyncio.fixture
async def async_client(override_get_db):
    app.dependency_overrides[get_async_session] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
