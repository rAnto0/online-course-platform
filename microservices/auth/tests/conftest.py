from fastapi import Depends
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import settings, AuthJWT, BASE_DIR
from app.models.users import User

pytest_plugins = ("tests.factories",)


@pytest.fixture(scope="session")
def faker():
    import faker

    return faker.Faker()


@pytest.fixture(scope="session", autouse=True)
def _configure_jwt_keys():
    private_key_path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path = BASE_DIR / "certs" / "jwt-public.pem"
    assert private_key_path.is_file(), "JWT private key not found in app/certs"
    assert public_key_path.is_file(), "JWT public key not found in app/certs"
    settings.AUTH_JWT_KEYS = AuthJWT(
        private_key_path=private_key_path,
        public_key_path=public_key_path,
    )
    settings.ALGORITHM = "RS256"
    settings.ENABLE_EVENTS = False


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


@pytest_asyncio.fixture
async def user_student(user_factory):
    """Создает пользователя с ролью студента"""
    return await user_factory()


@pytest_asyncio.fixture
async def auth_client_student(async_client, user_student):
    """
    Переопределяем dependency, который возвращает current user, на нашу фикстуру.
    """
    from app.services import auth as auth_service_module
    from app.routers.auth import oauth2_scheme

    class _AuthService(auth_service_module.AuthService):
        async def get_current_auth_user(self, token: str) -> User:
            result = await self.session.execute(
                select(User).where(User.id == user_student.id)
            )
            user = result.scalars().first()
            assert user is not None
            return user

    async def _override_get_auth_service(
        session: AsyncSession = Depends(get_async_session),
    ) -> auth_service_module.AuthService:
        return _AuthService(session=session)

    app.dependency_overrides[auth_service_module.get_auth_service] = (
        _override_get_auth_service
    )
    app.dependency_overrides[oauth2_scheme] = lambda: "test-token"

    yield async_client

    app.dependency_overrides.pop(auth_service_module.get_auth_service, None)
    app.dependency_overrides.pop(oauth2_scheme, None)
