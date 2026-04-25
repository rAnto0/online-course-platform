from uuid import UUID, uuid4

from httpx import AsyncClient

from tests.helpers import assert_course_progress_in_db


async def test_get_course_progress_not_found(
    async_client: AsyncClient,
):
    resp = await async_client.get(
        f"/progress/course-progress/courses/{uuid4()}",
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 404


async def test_get_course_progress_success(
    async_client: AsyncClient,
    course_progress_factory,
):
    user_id = uuid4()
    course_progress = await course_progress_factory(user_id=user_id)

    resp = await async_client.get(
        f"/progress/course-progress/courses/{course_progress.course_id}",
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["id"] == str(course_progress.id)
    assert body["course_id"] == str(course_progress.course_id)
    assert body["user_id"] == str(user_id)


async def test_upsert_course_progress_create_and_update(
    async_client: AsyncClient,
    course_progress_upsert_data_factory,
    db_session,
):
    user_id = uuid4()
    course_id = uuid4()

    create_payload = course_progress_upsert_data_factory(progress_percent=10)
    create_resp = await async_client.put(
        f"/progress/course-progress/courses/{course_id}",
        json=create_payload,
        headers={"X-User-Id": str(user_id)},
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["progress_percent"] == 10

    update_payload = course_progress_upsert_data_factory(
        total_lessons=25,
        progress_percent=80,
        last_lesson_id=str(uuid4()),
    )
    update_resp = await async_client.put(
        f"/progress/course-progress/courses/{course_id}",
        json=update_payload,
        headers={"X-User-Id": str(user_id)},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()

    assert updated["id"] == created["id"]
    assert updated["progress_percent"] == 80
    assert updated["total_lessons"] == 25
    assert updated["last_lesson_id"] == update_payload["last_lesson_id"]

    await assert_course_progress_in_db(
        db_session=db_session,
        course_progress_id=UUID(updated["id"]),
        user_id=user_id,
        course_id=course_id,
        progress_percent=80,
    )


async def test_upsert_course_progress_empty_body(
    async_client: AsyncClient,
):
    resp = await async_client.put(
        f"/progress/course-progress/courses/{uuid4()}",
        json={},
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 400


async def test_upsert_course_progress_validation_error_progress_percent(
    async_client: AsyncClient,
    course_progress_upsert_data_factory,
):
    resp = await async_client.put(
        f"/progress/course-progress/courses/{uuid4()}",
        json=course_progress_upsert_data_factory(progress_percent=101),
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 422
