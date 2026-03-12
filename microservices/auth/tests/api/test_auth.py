import pytest
from httpx import AsyncClient

from app.core.security import get_password_hash
from tests.helpers import assert_user_in_db


async def test_register_user_success(
    async_client: AsyncClient,
    user_registration_data_factory,
    db_session,
):
    """Успешная регистрация пользователя"""
    registration_data = user_registration_data_factory()

    resp = await async_client.post("/auth/register", json=registration_data)
    assert resp.status_code == 201
    data = resp.json()

    assert data["username"] == registration_data["username"]
    assert data["email"] == registration_data["email"]
    assert "id" in data
    assert "hashed_password" not in data

    await assert_user_in_db(
        db_session=db_session,
        username=registration_data["username"],
        email=registration_data["email"],
        password=registration_data["password"],
    )


async def test_register_user_duplicate_username(
    async_client: AsyncClient,
    user_factory,
    user_registration_data_factory,
):
    """Регистрация с существующим username"""
    await user_factory(username="existing_user")

    registration_data = user_registration_data_factory(username="existing_user")

    resp = await async_client.post("/auth/register", json=registration_data)
    assert resp.status_code == 400
    assert "detail" in resp.json()


async def test_register_user_duplicate_email(
    async_client: AsyncClient,
    user_factory,
    user_registration_data_factory,
):
    """Регистрация с существующим email"""
    await user_factory(email="existing@example.com")

    registration_data = user_registration_data_factory(email="existing@example.com")

    resp = await async_client.post("/auth/register", json=registration_data)
    assert resp.status_code == 400
    assert "detail" in resp.json()


async def test_register_user_validation_errors(
    async_client: AsyncClient,
    user_registration_data_factory,
):
    """Ошибки валидации при регистрации"""
    # Слишком короткий username
    data = user_registration_data_factory(username="ab")
    resp = await async_client.post("/auth/register", json=data)
    assert resp.status_code == 422

    # Неверный email
    data = user_registration_data_factory(email="invalid-email")
    resp = await async_client.post("/auth/register", json=data)
    assert resp.status_code == 422

    # Слишком короткий пароль
    data = user_registration_data_factory(password="12")
    resp = await async_client.post("/auth/register", json=data)
    assert resp.status_code == 422


async def test_login_user_success(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Успешный вход пользователя"""
    password = "SecurePass123!"
    await user_factory(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash(password),
    )

    login_data = user_login_data_factory(username="testuser", password=password)

    resp = await async_client.post("/auth/login", data=login_data)
    assert resp.status_code == 200
    data = resp.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


async def test_login_user_wrong_password(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Вход с неверным паролем"""
    await user_factory(username="testuser")

    login_data = user_login_data_factory(
        username="testuser", password="WrongPassword123!"
    )

    resp = await async_client.post("/auth/login", data=login_data)
    assert resp.status_code == 401


async def test_login_user_not_found(
    async_client: AsyncClient,
    user_login_data_factory,
):
    """Вход несуществующего пользователя"""
    login_data = user_login_data_factory(
        username="nonexistent", password="SomePass123!"
    )

    resp = await async_client.post("/auth/login", data=login_data)
    assert resp.status_code == 401


async def test_login_validation_errors(async_client: AsyncClient):
    """Ошибки валидации при логине"""
    resp = await async_client.post("/auth/login", data={})
    assert resp.status_code == 422

    resp = await async_client.post("/auth/login", data={"username": "user"})
    assert resp.status_code == 422

    resp = await async_client.post("/auth/login", data={"password": "pass"})
    assert resp.status_code == 422


async def test_get_current_user_success(
    auth_client_student,
    user_student,
):
    """Успешное получение текущего пользователя"""
    resp = await auth_client_student.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == str(user_student.id)
    assert data["username"] == user_student.username
    assert data["email"] == user_student.email
    assert "hashed_password" not in data


async def test_get_current_user_unauthorized(
    async_client: AsyncClient,
):
    """Получение текущего пользователя без аутентификации"""
    resp = await async_client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"


async def test_refresh_token_success(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Успешное обновление токена"""
    password = "SecurePass123!"
    await user_factory(username="testuser", hashed_password=get_password_hash(password))

    login_data = user_login_data_factory(username="testuser", password=password)
    login_resp = await async_client.post("/auth/login", data=login_data)
    refresh_token = (
        f"{login_resp.json()['token_type']} {login_resp.json()['refresh_token']}"
    )

    resp = await async_client.post(
        "/auth/refresh", headers={"Authorization": refresh_token}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


async def test_refresh_token_wrong_token_type(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Использование access токена для refresh"""
    password = "SecurePass123!"
    await user_factory(username="testuser", hashed_password=get_password_hash(password))

    login_data = user_login_data_factory(username="testuser", password=password)
    login_resp = await async_client.post("/auth/login", data=login_data)
    access_token = (
        f"{login_resp.json()['token_type']} {login_resp.json()['access_token']}"
    )

    resp = await async_client.post(
        "/auth/refresh", headers={"Authorization": access_token}
    )
    assert resp.status_code == 401


async def test_refresh_token_invalid(
    async_client: AsyncClient,
):
    """Обновление токена с невалидным refresh token"""
    resp = await async_client.post(
        "/auth/refresh", headers={"Authorization": "Bearer invalid_token"}
    )
    assert resp.status_code == 401
