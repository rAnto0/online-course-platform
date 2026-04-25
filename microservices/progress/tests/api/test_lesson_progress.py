from datetime import datetime
from uuid import UUID, uuid4

from httpx import AsyncClient

from app.models.enums import LessonProgressStatus
from tests.helpers import assert_lesson_progress_in_db


async def test_get_lesson_progress_not_found(async_client: AsyncClient):
    resp = await async_client.get(
        f"/progress/lesson-progress/lessons/{uuid4()}",
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 404


async def test_get_lesson_progress_success(
    async_client: AsyncClient,
    lesson_progress_factory,
):
    user_id = uuid4()
    lesson_progress = await lesson_progress_factory(user_id=user_id)

    resp = await async_client.get(
        f"/progress/lesson-progress/lessons/{lesson_progress.lesson_id}",
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["id"] == str(lesson_progress.id)
    assert body["lesson_id"] == str(lesson_progress.lesson_id)
    assert body["user_id"] == str(user_id)


async def test_upsert_lesson_progress_create_and_complete(
    async_client: AsyncClient,
    lesson_progress_upsert_data_factory,
    db_session,
):
    user_id = uuid4()
    lesson_id = uuid4()

    create_payload = lesson_progress_upsert_data_factory(
        status=LessonProgressStatus.IN_PROGRESS.value,
        progress_percent=35,
    )
    create_resp = await async_client.put(
        f"/progress/lesson-progress/lessons/{lesson_id}",
        json=create_payload,
        headers={"X-User-Id": str(user_id)},
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["status"] == LessonProgressStatus.IN_PROGRESS.value
    assert created["started_at"] is not None
    assert created["completed_at"] is None

    update_payload = lesson_progress_upsert_data_factory(
        course_id=create_payload["course_id"],
        section_id=create_payload["section_id"],
        status=LessonProgressStatus.COMPLETED.value,
        progress_percent=100,
    )
    update_resp = await async_client.put(
        f"/progress/lesson-progress/lessons/{lesson_id}",
        json=update_payload,
        headers={"X-User-Id": str(user_id)},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["id"] == created["id"]
    assert updated["status"] == LessonProgressStatus.COMPLETED.value
    assert updated["started_at"] is not None
    assert updated["completed_at"] is not None
    assert updated["progress_percent"] == 100

    await assert_lesson_progress_in_db(
        db_session=db_session,
        lesson_progress_id=UUID(updated["id"]),
        user_id=user_id,
        lesson_id=lesson_id,
        progress_percent=100,
    )


async def test_upsert_lesson_progress_update_to_not_started_resets_dates(
    async_client: AsyncClient,
    lesson_progress_factory,
):
    user_id = uuid4()
    lesson_id = uuid4()
    lesson_progress = await lesson_progress_factory(
        user_id=user_id,
        lesson_id=lesson_id,
        status=LessonProgressStatus.COMPLETED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )

    resp = await async_client.put(
        f"/progress/lesson-progress/lessons/{lesson_id}",
        json={
            "course_id": str(lesson_progress.course_id),
            "section_id": str(lesson_progress.section_id),
            "status": LessonProgressStatus.NOT_STARTED.value,
            "progress_percent": 0,
        },
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == LessonProgressStatus.NOT_STARTED.value
    assert body["started_at"] is None
    assert body["completed_at"] is None


async def test_get_lesson_progress_by_ids_success(
    async_client: AsyncClient,
    lesson_progress_factory,
):
    user_id = uuid4()
    lesson_a = await lesson_progress_factory(user_id=user_id)
    lesson_b = await lesson_progress_factory(user_id=user_id)
    missing_id = uuid4()

    resp = await async_client.post(
        "/progress/lesson-progress/lessons/by-ids",
        json={
            "lesson_ids": [
                str(lesson_a.lesson_id),
                str(lesson_b.lesson_id),
                str(missing_id),
            ]
        },
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["found"]) == 2
    assert set(item["lesson_id"] for item in body["found"]) == {
        str(lesson_a.lesson_id),
        str(lesson_b.lesson_id),
    }
    assert body["missing"] == [str(missing_id)]


async def test_get_lesson_progress_by_ids_duplicates(
    async_client: AsyncClient,
    lesson_progress_factory,
):
    user_id = uuid4()
    lesson = await lesson_progress_factory(user_id=user_id)
    lesson_id = str(lesson.lesson_id)

    resp = await async_client.post(
        "/progress/lesson-progress/lessons/by-ids",
        json={"lesson_ids": [lesson_id, lesson_id, lesson_id]},
        headers={"X-User-Id": str(user_id)},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["found"]) == 1
    assert body["found"][0]["lesson_id"] == lesson_id
    assert body["missing"] == []


async def test_get_lesson_progress_by_ids_validation_error(
    async_client: AsyncClient,
):
    resp = await async_client.post(
        "/progress/lesson-progress/lessons/by-ids",
        json={"lesson_ids": []},
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 422


async def test_get_lesson_progress_by_ids_limit_exceeded(
    async_client: AsyncClient,
):
    resp = await async_client.post(
        "/progress/lesson-progress/lessons/by-ids",
        json={"lesson_ids": [str(uuid4()) for _ in range(101)]},
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 422


async def test_get_lesson_progress_by_ids_invalid_uuid(
    async_client: AsyncClient,
):
    resp = await async_client.post(
        "/progress/lesson-progress/lessons/by-ids",
        json={"lesson_ids": ["not-a-uuid"]},
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 422


async def test_upsert_lesson_progress_validation_error_progress_percent(
    async_client: AsyncClient,
    lesson_progress_upsert_data_factory,
):
    resp = await async_client.put(
        f"/progress/lesson-progress/lessons/{uuid4()}",
        json=lesson_progress_upsert_data_factory(progress_percent=101),
        headers={"X-User-Id": str(uuid4())},
    )
    assert resp.status_code == 422
