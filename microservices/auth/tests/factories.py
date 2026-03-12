import pytest
import pytest_asyncio

from app.core.security import get_password_hash
from app.models.users import User


@pytest_asyncio.fixture
async def user_factory(db_session, faker):
    """Фабрика для создания тестовых пользователей"""

    async def _factory(**kwargs):
        defaults = {
            "username": f"testuser_{faker.user_name()}",
            "email": f"test_{faker.word()}@example.com",
            "hashed_password": get_password_hash("TestPass123!"),
        }
        user_data = {**defaults, **kwargs}

        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _factory


@pytest.fixture
def user_registration_data_factory(faker):
    """Фабрика данных для регистрации пользователя"""

    def _factory(**kwargs):
        base_data = {
            "username": f"testuser_{faker.user_name()}",
            "email": f"test_{faker.word()}@example.com",
            "password": "SecurePass123!",
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def user_login_data_factory():
    """Фабрика данных для входа пользователя"""

    def _factory(**kwargs):
        base_data = {"username": "testuser", "password": "SecurePass123!"}
        return {**base_data, **kwargs}

    return _factory
