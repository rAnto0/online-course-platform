import os

import httpx
import pytest

BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080")
USER = os.getenv("GATEWAY_USER", "")
PASS = os.getenv("GATEWAY_PASS", "")


def _client():
    return httpx.Client(base_url=BASE_URL, timeout=5.0)


def _assert_status_in(resp: httpx.Response, expected: set[int]) -> None:
    assert resp.status_code in expected, resp.text


def _get_paginated(client: httpx.Client, path: str, params: dict | None = None) -> dict:
    resp = client.get(path, params=params)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert isinstance(data["total"], int)
    assert "skip" in data
    assert "limit" in data
    return data


def test_auth_health():
    with _client() as client:
        resp = client.get("/auth/health")
    assert resp.status_code == 200


def test_categories_list_with_query():
    with _client() as client:
        page = _get_paginated(client, "/categories", params={"skip": 0, "limit": 2})
    assert len(page["items"]) <= 2
    assert page["total"] >= len(page["items"])


def test_courses_list_with_query():
    with _client() as client:
        page = _get_paginated(client, "/courses", params={"skip": 0, "limit": 2})
    assert len(page["items"]) <= 2
    assert page["total"] >= len(page["items"])


def test_categories_by_id_and_slug():
    with _client() as client:
        items = _get_paginated(client, "/categories", params={"skip": 0, "limit": 1})[
            "items"
        ]
        if not items:
            pytest.skip("No categories to test by id/slug")
        category = items[0]
        category_id = category.get("id")
        slug = category.get("slug")
        assert category_id
        assert slug

        by_id = client.get(f"/categories/{category_id}")
        _assert_status_in(by_id, {200})

        by_slug = client.get(f"/categories/by-slug/{slug}")
        _assert_status_in(by_slug, {200})


def test_courses_and_nested_sections_lessons():
    with _client() as client:
        courses = _get_paginated(client, "/courses", params={"skip": 0, "limit": 1})[
            "items"
        ]
        if not courses:
            pytest.skip("No courses to test nested routes")
        course_id = courses[0].get("id")
        assert course_id

        course = client.get(f"/courses/{course_id}")
        _assert_status_in(course, {200})

        sections = _get_paginated(
            client,
            f"/courses/{course_id}/sections",
            params={"skip": 0, "limit": 1},
        )["items"]
        if not sections:
            pytest.skip("No sections to test lessons routes")
        section_id = sections[0].get("id")
        assert section_id

        section = client.get(f"/courses/{course_id}/sections/{section_id}")
        _assert_status_in(section, {200})

        lessons = _get_paginated(
            client,
            f"/courses/{course_id}/sections/{section_id}/lessons",
            params={"skip": 0, "limit": 1},
        )["items"]
        if not lessons:
            pytest.skip("No lessons to test lesson detail route")
        lesson_id = lessons[0].get("id")
        assert lesson_id

        lesson = client.get(
            f"/courses/{course_id}/sections/{section_id}/lessons/{lesson_id}"
        )
        _assert_status_in(lesson, {200})


def test_protected_endpoints_require_auth():
    with _client() as client:
        # Auth endpoints
        _assert_status_in(client.get("/auth/me"), {401, 403})
        _assert_status_in(client.post("/auth/refresh"), {401, 403})

        # Category mutations
        _assert_status_in(client.post("/categories", json={"name": "tmp"}), {401, 403})
        _assert_status_in(client.put("/categories/00000000-0000-0000-0000-000000000000", json={"name": "tmp"}), {401, 403})
        _assert_status_in(client.delete("/categories/00000000-0000-0000-0000-000000000000"), {401, 403})

        # Course mutations
        _assert_status_in(client.post("/courses", json={"title": "tmp"}), {401, 403})
        _assert_status_in(client.put("/courses/00000000-0000-0000-0000-000000000000", json={"title": "tmp"}), {401, 403})
        _assert_status_in(client.delete("/courses/00000000-0000-0000-0000-000000000000"), {401, 403})
        _assert_status_in(client.patch("/courses/00000000-0000-0000-0000-000000000000/publish"), {401, 403})
        _assert_status_in(client.patch("/courses/00000000-0000-0000-0000-000000000000/archive"), {401, 403})


@pytest.mark.skipif(not USER or not PASS, reason="GATEWAY_USER/GATEWAY_PASS not set")
def test_auth_me_with_token():
    with _client() as client:
        login = client.post(
            "/auth/login",
            data={"username": USER, "password": PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login.status_code == 200
        token = login.json().get("access_token")
        assert token

        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
