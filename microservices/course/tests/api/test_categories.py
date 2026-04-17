from uuid import uuid4

from httpx import AsyncClient

from tests.helpers import assert_category_in_db


async def test_list_categories_empty(async_client: AsyncClient):
    resp = await async_client.get("/categories/")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0, "skip": 0, "limit": 100}


async def test_list_categories_pagination_total(
    async_client: AsyncClient,
    category_factory,
):
    await category_factory()
    await category_factory()

    resp = await async_client.get("/categories/", params={"skip": 0, "limit": 1})
    assert resp.status_code == 200
    body = resp.json()

    assert body["skip"] == 0
    assert body["limit"] == 1
    assert body["total"] == 2
    assert len(body["items"]) == 1


async def test_get_category_not_found(async_client: AsyncClient):
    resp = await async_client.get(f"/categories/{uuid4()}")
    assert resp.status_code == 404


async def test_create_category_forbidden_non_admin(
    auth_client_student: AsyncClient,
    category_create_data_factory,
):
    data = category_create_data_factory()
    resp = await auth_client_student.post("/categories/", json=data)
    assert resp.status_code == 403


async def test_create_category_unauthorized(
    async_client: AsyncClient,
    category_create_data_factory,
):
    data = category_create_data_factory()
    resp = await async_client.post("/categories/", json=data)
    assert resp.status_code == 401


async def test_create_category_admin_success(
    auth_client_admin: AsyncClient,
    category_create_data_factory,
    db_session,
):
    data = category_create_data_factory()
    resp = await auth_client_admin.post("/categories/", json=data)
    assert resp.status_code == 201
    body = resp.json()

    assert body["name"] == data["name"]
    assert "id" in body
    assert "slug" in body

    await assert_category_in_db(db_session=db_session, name=data["name"])


async def test_create_category_duplicate_name(
    auth_client_admin: AsyncClient,
    category_factory,
    category_create_data_factory,
):
    existing = await category_factory()
    data = category_create_data_factory(name=existing.name)
    resp = await auth_client_admin.post("/categories/", json=data)
    assert resp.status_code == 409


async def test_create_category_validation_error(
    auth_client_admin: AsyncClient,
):
    resp = await auth_client_admin.post("/categories/", json={"name": ""})
    assert resp.status_code == 422


async def test_update_category_admin_success(
    auth_client_admin: AsyncClient,
    category_factory,
    category_update_data_factory,
):
    category = await category_factory()
    data = category_update_data_factory()
    resp = await auth_client_admin.put(f"/categories/{category.id}", json=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(category.id)
    assert body["name"] == data["name"]


async def test_update_category_unauthorized(
    async_client: AsyncClient,
    category_factory,
):
    category = await category_factory()
    resp = await async_client.put(
        f"/categories/{category.id}",
        json={"name": "Updated"},
    )
    assert resp.status_code == 401


async def test_update_category_forbidden_non_admin(
    auth_client_student: AsyncClient,
    category_factory,
):
    category = await category_factory()
    resp = await auth_client_student.put(
        f"/categories/{category.id}",
        json={"name": "Updated"},
    )
    assert resp.status_code == 403


async def test_update_category_not_found(
    auth_client_admin: AsyncClient,
):
    resp = await auth_client_admin.put(
        f"/categories/{uuid4()}",
        json={"name": "Updated"},
    )
    assert resp.status_code == 404


async def test_update_category_duplicate_name(
    auth_client_admin: AsyncClient,
    category_factory,
    category_update_data_factory,
):
    existing = await category_factory()
    other = await category_factory()
    data = category_update_data_factory(name=existing.name)
    resp = await auth_client_admin.put(f"/categories/{other.id}", json=data)
    assert resp.status_code == 409


async def test_get_category_by_slug(
    async_client: AsyncClient,
    category_factory,
):
    category = await category_factory()
    resp = await async_client.get(f"/categories/by-slug/{category.slug}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(category.id)
    assert body["slug"] == category.slug


async def test_delete_category_admin_success(
    auth_client_admin: AsyncClient,
    category_factory,
):
    category = await category_factory()
    resp = await auth_client_admin.delete(f"/categories/{category.id}")
    assert resp.status_code == 204


async def test_delete_category_unauthorized(
    async_client: AsyncClient,
    category_factory,
):
    category = await category_factory()
    resp = await async_client.delete(f"/categories/{category.id}")
    assert resp.status_code == 401


async def test_delete_category_forbidden_non_admin(
    auth_client_student: AsyncClient,
    category_factory,
):
    category = await category_factory()
    resp = await auth_client_student.delete(f"/categories/{category.id}")
    assert resp.status_code == 403


async def test_delete_category_not_found(
    auth_client_admin: AsyncClient,
):
    resp = await auth_client_admin.delete(f"/categories/{uuid4()}")
    assert resp.status_code == 404
