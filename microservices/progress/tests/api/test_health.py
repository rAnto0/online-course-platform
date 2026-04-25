from httpx import AsyncClient

from app.core.database import get_async_session
from app.main import app


async def test_root(async_client: AsyncClient):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Welcome to the Progress service"}


async def test_health_ok(async_client: AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_health_db_error_returns_503(async_client: AsyncClient):
    class BrokenSession:
        async def execute(self, *_args, **_kwargs):
            raise RuntimeError("db is down")

    async def _broken_get_db():
        yield BrokenSession()

    previous_override = app.dependency_overrides.get(get_async_session)
    app.dependency_overrides[get_async_session] = _broken_get_db
    try:
        resp = await async_client.get("/health")
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_async_session, None)
        else:
            app.dependency_overrides[get_async_session] = previous_override

    assert resp.status_code == 503
    assert resp.json() == {"status": "error"}
