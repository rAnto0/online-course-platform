from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import settings, BASE_DIR
from app.dependencies.auth import get_current_user

pytest_plugins = ("tests.factories",)


@pytest.fixture(scope="session")
def faker():
    import faker

    return faker.Faker()


@pytest.fixture(scope="session", autouse=True)
def _configure_jwt_keys():
    public_key_path = BASE_DIR / "core" / "certs" / "jwt-public.pem"
    assert public_key_path.is_file(), "JWT public key not found in app/core/certs"
    settings.AUTH_JWT_PUBLIC_KEY = public_key_path
    settings.ALGORITHM = "RS256"


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        settings.DATABASE_TEST_URL, echo=False, poolclass=NullPool
    )
    # создаём схему один раз
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    # открываем connection и стартуем глобальную транзакцию
    async with async_engine.connect() as conn:
        trans = await conn.begin()  # outer transaction

        # фабрика сессий, привязанная к открытому connection
        async_session = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )

        async with async_session() as session:
            # стартуем nested transaction (SAVEPOINT) для теста
            await session.begin_nested()

            # слушатель для автоматического восстановления nested savepoint после отката
            def _restart_savepoint(session_, transaction):
                # если вложенная транзакция закончилась (rollback/commit),
                # и сейчас мы не в nested транзакции — создаём новый savepoint
                if not session_.in_nested_transaction():
                    session_.begin_nested()

            event.listen(
                session.sync_session, "after_transaction_end", _restart_savepoint
            )

            try:
                yield session
            finally:
                # удаляем слушатель чтобы избежать побочных эффектов
                event.remove(
                    session.sync_session, "after_transaction_end", _restart_savepoint
                )

                # закрываем сессию и откатываем outer транзакцию
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


@pytest.fixture
def user_student(user_factory):
    return user_factory(role="student")


@pytest.fixture
def user_teacher(user_factory):
    return user_factory(role="teacher")


@pytest.fixture
def user_admin(user_factory):
    return user_factory(role="admin")


@pytest.fixture
def user_owner(user_factory):
    return user_factory(role="teacher")


@pytest_asyncio.fixture
async def auth_client_factory(async_client):
    @asynccontextmanager
    async def _factory(user: dict):
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            yield async_client
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    return _factory


@pytest_asyncio.fixture
async def auth_client_student(async_client, user_student):
    app.dependency_overrides[get_current_user] = lambda: user_student
    yield async_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def auth_client_teacher(async_client, user_teacher):
    app.dependency_overrides[get_current_user] = lambda: user_teacher
    yield async_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def auth_client_admin(async_client, user_admin):
    app.dependency_overrides[get_current_user] = lambda: user_admin
    yield async_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def auth_client_owner(async_client, user_owner):
    app.dependency_overrides[get_current_user] = lambda: user_owner
    yield async_client
    app.dependency_overrides.pop(get_current_user, None)
