from datetime import datetime
from uuid import UUID, uuid4

from httpx import AsyncClient

from app.models.enums import EnrollmentStatus
from tests.helpers import assert_enrollment_in_db


async def test_create_enrollment_success(
    async_client: AsyncClient,
    enrollment_create_data_factory,
    db_session,
):
    user_id = uuid4()
    payload = enrollment_create_data_factory()

    resp = await async_client.post(
        "/progress/enrollments",
        json=payload,
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 201
    body = resp.json()

    assert body["course_id"] == payload["course_id"]
    assert body["user_id"] == str(user_id)
    assert body["status"] == EnrollmentStatus.ACTIVE.value
    assert body["completed_at"] is None

    await assert_enrollment_in_db(
        db_session=db_session,
        enrollment_id=UUID(body["id"]),
        user_id=user_id,
        course_id=UUID(payload["course_id"]),
        status=EnrollmentStatus.ACTIVE,
    )


async def test_create_enrollment_completed_sets_completed_at(
    async_client: AsyncClient,
    enrollment_create_data_factory,
):
    user_id = uuid4()
    payload = enrollment_create_data_factory(status=EnrollmentStatus.COMPLETED.value)

    resp = await async_client.post(
        "/progress/enrollments",
        json=payload,
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 201
    body = resp.json()

    assert body["status"] == EnrollmentStatus.COMPLETED.value
    assert body["completed_at"] is not None


async def test_create_enrollment_duplicate_conflict(
    async_client: AsyncClient,
    enrollment_create_data_factory,
):
    user_id = uuid4()
    payload = enrollment_create_data_factory()
    headers = {"X-User-Id": str(user_id)}

    first = await async_client.post(
        "/progress/enrollments",
        json=payload,
        headers=headers,
    )
    assert first.status_code == 201

    second = await async_client.post(
        "/progress/enrollments",
        json=payload,
        headers=headers,
    )
    assert second.status_code == 409


async def test_create_enrollment_without_user_header_validation_error(
    async_client: AsyncClient,
    enrollment_create_data_factory,
):
    resp = await async_client.post(
        "/progress/enrollments",
        json=enrollment_create_data_factory(),
    )
    assert resp.status_code == 422


async def test_list_enrollments_by_user(
    async_client: AsyncClient,
    enrollment_factory,
):
    user_id = uuid4()
    await enrollment_factory(user_id=user_id)
    await enrollment_factory(user_id=user_id)
    await enrollment_factory(user_id=uuid4())

    resp = await async_client.get(
        "/progress/enrollments/by-user",
        params={"skip": 0, "limit": 1},
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert len(body) == 1
    assert all(item["user_id"] == str(user_id) for item in body)


async def test_get_enrollment_by_id_not_found(async_client: AsyncClient):
    resp = await async_client.get(f"/progress/enrollments/{uuid4()}")
    assert resp.status_code == 404


async def test_get_enrollment_by_id_success(
    async_client: AsyncClient,
    enrollment_factory,
):
    enrollment = await enrollment_factory()
    resp = await async_client.get(f"/progress/enrollments/{enrollment.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(enrollment.id)
    assert body["course_id"] == str(enrollment.course_id)
    assert body["user_id"] == str(enrollment.user_id)


async def test_get_enrollment_by_user_course_success(
    async_client: AsyncClient,
    enrollment_factory,
):
    user_id = uuid4()
    enrollment = await enrollment_factory(user_id=user_id)

    resp = await async_client.get(
        f"/progress/enrollments/by-course/{enrollment.course_id}",
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["id"] == str(enrollment.id)
    assert body["course_id"] == str(enrollment.course_id)
    assert body["user_id"] == str(user_id)


async def test_get_enrollment_by_user_course_not_found(
    async_client: AsyncClient,
):
    resp = await async_client.get(
        f"/progress/enrollments/by-course/{uuid4()}",
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 404


async def test_update_enrollment_status_completed(
    async_client: AsyncClient,
    enrollment_factory,
):
    enrollment = await enrollment_factory(status=EnrollmentStatus.ACTIVE)

    resp = await async_client.patch(
        f"/progress/enrollments/{enrollment.id}",
        json={"status": EnrollmentStatus.COMPLETED.value},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == EnrollmentStatus.COMPLETED.value
    assert body["completed_at"] is not None


async def test_update_enrollment_status_active_resets_completed_at(
    async_client: AsyncClient,
    enrollment_factory,
):
    enrollment = await enrollment_factory(
        status=EnrollmentStatus.COMPLETED,
        completed_at=datetime.utcnow(),
    )

    resp = await async_client.patch(
        f"/progress/enrollments/{enrollment.id}",
        json={"status": EnrollmentStatus.ACTIVE.value},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == EnrollmentStatus.ACTIVE.value
    assert body["completed_at"] is None


async def test_update_enrollment_empty_body(
    async_client: AsyncClient,
    enrollment_factory,
):
    enrollment = await enrollment_factory()
    resp = await async_client.patch(f"/progress/enrollments/{enrollment.id}", json={})
    assert resp.status_code == 400


async def test_update_enrollment_not_found(async_client: AsyncClient):
    resp = await async_client.patch(
        f"/progress/enrollments/{uuid4()}",
        json={"status": EnrollmentStatus.ACTIVE.value},
    )
    assert resp.status_code == 404
