from uuid import uuid4

from httpx import AsyncClient

from tests.helpers import assert_course_in_db


async def test_list_courses_empty(async_client: AsyncClient):
    resp = await async_client.get("/courses/")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0, "skip": 0, "limit": 100}


async def test_list_courses_pagination_total(
    async_client: AsyncClient,
    course_factory,
):
    await course_factory()
    await course_factory()

    resp = await async_client.get("/courses/", params={"skip": 0, "limit": 1})
    assert resp.status_code == 200
    body = resp.json()

    assert body["skip"] == 0
    assert body["limit"] == 1
    assert body["total"] == 2
    assert len(body["items"]) == 1


async def test_get_course_not_found(async_client: AsyncClient):
    resp = await async_client.get(f"/courses/{uuid4()}")
    assert resp.status_code == 404


async def test_create_course_unauthorized(
    async_client: AsyncClient,
    course_create_data_factory,
):
    data = course_create_data_factory()
    resp = await async_client.post("/courses/", json=data)
    assert resp.status_code == 401


async def test_create_course_success(
    auth_client_student: AsyncClient,
    course_create_data_factory,
    user_student,
    db_session,
):
    data = course_create_data_factory()
    resp = await auth_client_student.post("/courses/", json=data)
    assert resp.status_code == 201
    body = resp.json()

    assert body["title"] == data["title"]
    assert body["description"] == data["description"]
    assert body["author_id"] == str(user_student["id"])
    assert body["status"] == "DRAFT"

    await assert_course_in_db(
        db_session=db_session,
        course_id=body["id"],
        title=data["title"],
        author_id=user_student["id"],
    )


async def test_create_course_validation_error(
    auth_client_owner: AsyncClient,
):
    resp = await auth_client_owner.post("/courses/", json={"title": ""})
    assert resp.status_code == 422


async def test_update_course_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    course_update_data_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    data = course_update_data_factory()

    resp = await auth_client_owner.put(f"/courses/{course.id}", json=data)
    assert resp.status_code == 200
    body = resp.json()

    assert body["id"] == str(course.id)
    assert body["title"] == data["title"]
    assert body["description"] == data["description"]


async def test_update_course_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
):
    course = await course_factory(author_id=uuid4())
    resp = await auth_client_teacher.put(
        f"/courses/{course.id}",
        json={"title": "Updated title"},
    )
    assert resp.status_code == 403


async def test_update_course_unauthorized(
    async_client: AsyncClient,
    course_factory,
):
    course = await course_factory()
    resp = await async_client.put(
        f"/courses/{course.id}",
        json={"title": "Updated title"},
    )
    assert resp.status_code == 401


async def test_update_course_not_found(
    auth_client_owner: AsyncClient,
):
    resp = await auth_client_owner.put(
        f"/courses/{uuid4()}",
        json={"title": "Updated title"},
    )
    assert resp.status_code == 404


async def test_delete_course_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    resp = await auth_client_owner.delete(f"/courses/{course.id}")
    assert resp.status_code == 204


async def test_delete_course_unauthorized(
    async_client: AsyncClient,
    course_factory,
):
    course = await course_factory()
    resp = await async_client.delete(f"/courses/{course.id}")
    assert resp.status_code == 401


async def test_delete_course_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
):
    course = await course_factory(author_id=uuid4())
    resp = await auth_client_teacher.delete(f"/courses/{course.id}")
    assert resp.status_code == 403


async def test_delete_course_not_found(
    auth_client_owner: AsyncClient,
):
    resp = await auth_client_owner.delete(f"/courses/{uuid4()}")
    assert resp.status_code == 404


async def test_publish_course_no_sections(
    auth_client_owner: AsyncClient,
    course_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    resp = await auth_client_owner.patch(f"/courses/{course.id}/publish")
    assert resp.status_code == 400


async def test_publish_course_unauthorized(
    async_client: AsyncClient,
    course_factory,
):
    course = await course_factory()
    resp = await async_client.patch(f"/courses/{course.id}/publish")
    assert resp.status_code == 401


async def test_publish_course_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
):
    course = await course_factory(author_id=uuid4())
    resp = await auth_client_teacher.patch(f"/courses/{course.id}/publish")
    assert resp.status_code == 403


async def test_publish_course_not_found(
    auth_client_owner: AsyncClient,
):
    resp = await auth_client_owner.patch(f"/courses/{uuid4()}/publish")
    assert resp.status_code == 404


async def test_publish_course_no_lessons(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    await section_factory(course_id=course.id)
    resp = await auth_client_owner.patch(f"/courses/{course.id}/publish")
    assert resp.status_code == 400


async def test_publish_course_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    await lesson_factory(section_id=section.id)

    resp = await auth_client_owner.patch(f"/courses/{course.id}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PUBLISHED"


async def test_publish_course_missing_fields(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
    user_owner,
):
    course = await course_factory(
        author_id=user_owner["id"],
        description=None,
        category_id=None,
        level=None,
    )
    section = await section_factory(course_id=course.id)
    await lesson_factory(section_id=section.id)

    resp = await auth_client_owner.patch(f"/courses/{course.id}/publish")
    assert resp.status_code == 400


async def test_archive_course_success(
    auth_client_owner: AsyncClient,
    course_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    resp = await auth_client_owner.patch(f"/courses/{course.id}/archive")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ARCHIVED"


async def test_archive_course_unauthorized(
    async_client: AsyncClient,
    course_factory,
):
    course = await course_factory()
    resp = await async_client.patch(f"/courses/{course.id}/archive")
    assert resp.status_code == 401


async def test_archive_course_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
):
    course = await course_factory(author_id=uuid4())
    resp = await auth_client_teacher.patch(f"/courses/{course.id}/archive")
    assert resp.status_code == 403


async def test_archive_course_not_found(
    auth_client_owner: AsyncClient,
):
    resp = await auth_client_owner.patch(f"/courses/{uuid4()}/archive")
    assert resp.status_code == 404


async def test_list_sections(
    async_client: AsyncClient,
    course_factory,
    section_factory,
):
    course = await course_factory()
    section = await section_factory(course_id=course.id)
    resp = await async_client.get(f"/courses/{course.id}/sections")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["skip"] == 0
    assert data["limit"] == 100
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(section.id)


async def test_list_sections_pagination_total(
    async_client: AsyncClient,
    course_factory,
    section_factory,
):
    course = await course_factory()
    await section_factory(course_id=course.id, position=0)
    await section_factory(course_id=course.id, position=1)

    resp = await async_client.get(
        f"/courses/{course.id}/sections", params={"skip": 1, "limit": 1}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 2
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert len(data["items"]) == 1


async def test_list_sections_course_not_found(async_client: AsyncClient):
    resp = await async_client.get(f"/courses/{uuid4()}/sections")
    assert resp.status_code == 404


async def test_create_section_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_create_data_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    data = section_create_data_factory()
    resp = await auth_client_owner.post(
        f"/courses/{course.id}/sections",
        json=data,
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == data["title"]


async def test_create_section_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
    section_create_data_factory,
):
    course = await course_factory(author_id=uuid4())
    data = section_create_data_factory()
    resp = await auth_client_teacher.post(
        f"/courses/{course.id}/sections",
        json=data,
    )
    assert resp.status_code == 403


async def test_update_section_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
    section_factory,
    section_update_data_factory,
):
    course = await course_factory(author_id=uuid4())
    section = await section_factory(course_id=course.id)
    data = section_update_data_factory()
    resp = await auth_client_teacher.put(
        f"/courses/{course.id}/sections/{section.id}",
        json=data,
    )
    assert resp.status_code == 403


async def test_delete_section_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
    section_factory,
):
    course = await course_factory(author_id=uuid4())
    section = await section_factory(course_id=course.id)
    resp = await auth_client_teacher.delete(
        f"/courses/{course.id}/sections/{section.id}"
    )
    assert resp.status_code == 403


async def test_update_section_not_found_in_course(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    section_update_data_factory,
    user_owner,
):
    course_a = await course_factory(author_id=user_owner["id"])
    course_b = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course_b.id)
    data = section_update_data_factory()
    resp = await auth_client_owner.put(
        f"/courses/{course_a.id}/sections/{section.id}",
        json=data,
    )
    assert resp.status_code == 404


async def test_create_section_validation_error(
    auth_client_owner: AsyncClient,
    course_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    resp = await auth_client_owner.post(
        f"/courses/{course.id}/sections",
        json={"title": ""},
    )
    assert resp.status_code == 422


async def test_update_section_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    section_update_data_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    data = section_update_data_factory()
    resp = await auth_client_owner.put(
        f"/courses/{course.id}/sections/{section.id}",
        json=data,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == data["title"]


async def test_delete_section_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    resp = await auth_client_owner.delete(f"/courses/{course.id}/sections/{section.id}")
    assert resp.status_code == 204


async def test_delete_section_not_found(
    auth_client_owner: AsyncClient,
    course_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    resp = await auth_client_owner.delete(
        f"/courses/{course.id}/sections/{uuid4()}"
    )
    assert resp.status_code == 404


async def test_list_lessons(
    async_client: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
):
    course = await course_factory()
    section = await section_factory(course_id=course.id)
    lesson = await lesson_factory(section_id=section.id)
    resp = await async_client.get(f"/courses/{course.id}/sections/{section.id}/lessons")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["skip"] == 0
    assert data["limit"] == 100
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(lesson.id)


async def test_list_lessons_pagination_total(
    async_client: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
):
    course = await course_factory()
    section = await section_factory(course_id=course.id)
    await lesson_factory(section_id=section.id, position=0)
    await lesson_factory(section_id=section.id, position=1)

    resp = await async_client.get(
        f"/courses/{course.id}/sections/{section.id}/lessons",
        params={"skip": 1, "limit": 1},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 2
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert len(data["items"]) == 1


async def test_list_lessons_course_not_found(async_client: AsyncClient):
    resp = await async_client.get(
        f"/courses/{uuid4()}/sections/{uuid4()}/lessons"
    )
    assert resp.status_code == 404


async def test_create_lesson_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    lesson_create_data_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    data = lesson_create_data_factory()
    resp = await auth_client_owner.post(
        f"/courses/{course.id}/sections/{section.id}/lessons",
        json=data,
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == data["title"]


async def test_create_lesson_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
    section_factory,
    lesson_create_data_factory,
):
    course = await course_factory(author_id=uuid4())
    section = await section_factory(course_id=course.id)
    data = lesson_create_data_factory()
    resp = await auth_client_teacher.post(
        f"/courses/{course.id}/sections/{section.id}/lessons",
        json=data,
    )
    assert resp.status_code == 403


async def test_update_lesson_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
    lesson_update_data_factory,
):
    course = await course_factory(author_id=uuid4())
    section = await section_factory(course_id=course.id)
    lesson = await lesson_factory(section_id=section.id)
    data = lesson_update_data_factory()
    resp = await auth_client_teacher.put(
        f"/courses/{course.id}/sections/{section.id}/lessons/{lesson.id}",
        json=data,
    )
    assert resp.status_code == 403


async def test_delete_lesson_forbidden_for_non_owner(
    auth_client_teacher: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
):
    course = await course_factory(author_id=uuid4())
    section = await section_factory(course_id=course.id)
    lesson = await lesson_factory(section_id=section.id)
    resp = await auth_client_teacher.delete(
        f"/courses/{course.id}/sections/{section.id}/lessons/{lesson.id}"
    )
    assert resp.status_code == 403


async def test_update_lesson_not_found_in_course(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
    lesson_update_data_factory,
    user_owner,
):
    course_a = await course_factory(author_id=user_owner["id"])
    course_b = await course_factory(author_id=user_owner["id"])
    section_b = await section_factory(course_id=course_b.id)
    lesson = await lesson_factory(section_id=section_b.id)
    data = lesson_update_data_factory()
    resp = await auth_client_owner.put(
        f"/courses/{course_a.id}/sections/{section_b.id}/lessons/{lesson.id}",
        json=data,
    )
    assert resp.status_code == 404


async def test_create_lesson_validation_error(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    resp = await auth_client_owner.post(
        f"/courses/{course.id}/sections/{section.id}/lessons",
        json={"title": ""},
    )
    assert resp.status_code == 422


async def test_update_lesson_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
    lesson_update_data_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    lesson = await lesson_factory(section_id=section.id)
    data = lesson_update_data_factory()
    resp = await auth_client_owner.put(
        f"/courses/{course.id}/sections/{section.id}/lessons/{lesson.id}",
        json=data,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == data["title"]


async def test_delete_lesson_owner_success(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    lesson_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    lesson = await lesson_factory(section_id=section.id)
    resp = await auth_client_owner.delete(
        f"/courses/{course.id}/sections/{section.id}/lessons/{lesson.id}"
    )
    assert resp.status_code == 204


async def test_delete_lesson_not_found(
    auth_client_owner: AsyncClient,
    course_factory,
    section_factory,
    user_owner,
):
    course = await course_factory(author_id=user_owner["id"])
    section = await section_factory(course_id=course.id)
    resp = await auth_client_owner.delete(
        f"/courses/{course.id}/sections/{section.id}/lessons/{uuid4()}"
    )
    assert resp.status_code == 404
