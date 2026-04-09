#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8080").rstrip("/")
USERNAME = os.environ.get("SEED_USERNAME", "Admin")
PASSWORD = os.environ.get("SEED_PASSWORD", "admin123")
COUNT = int(os.environ.get("SEED_COUNT", "100"))
PUBLISH = os.environ.get("SEED_PUBLISH", "true").lower() in {"1", "true", "yes", "y"}
DATA_FILE = os.environ.get("SEED_DATA_FILE", "scripts/seed_courses.json")


def _normalize_collection(payload):
    if isinstance(payload, dict) and isinstance(payload.get("collection"), list):
        return payload["collection"]
    if isinstance(payload, list):
        return payload
    return []


def request(method, path, token=None, data=None, content_type="application/json"):
    url = f"{BASE_URL}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        if content_type == "application/json":
            body = json.dumps(data).encode("utf-8")
        else:
            body = data
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as err:
        raw = err.read()
        message = raw.decode("utf-8") if raw else str(err)
        raise RuntimeError(f"{method} {path} -> {err.code}: {message}") from err


def login():
    form = urllib.parse.urlencode({"username": USERNAME, "password": PASSWORD}).encode("utf-8")
    return request("POST", "/auth/login", data=form, content_type="application/x-www-form-urlencoded")


def ensure_token():
    try:
        data = login()
        return data["access_token"]
    except Exception as err:
        raise RuntimeError(
            "Cannot login. Provide admin credentials via SEED_USERNAME/SEED_PASSWORD."
        ) from err


def ensure_admin(token):
    me = request("GET", "/auth/me", token=token)
    role = me.get("role") if isinstance(me, dict) else None
    if role != "admin":
        raise RuntimeError(f"User '{USERNAME}' is not admin (role={role}).")


def load_seed_data():
    if not os.path.exists(DATA_FILE):
        raise RuntimeError(f"Seed data file not found: {DATA_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_categories(token, categories):
    existing = request("GET", "/categories?skip=0&limit=10000")
    existing_list = _normalize_collection(existing)
    by_name = {c["name"].lower(): c for c in existing_list if "name" in c}

    for item in categories:
        name = item.get("name", "").strip()
        if not name:
            continue
        if name.lower() in by_name:
            print(f"[seed] category exists: {name}")
            continue
        try:
            created = request("POST", "/categories", token=token, data={"name": name})
            by_name[name.lower()] = created
        except Exception as err:
            print(f"[warn] cannot create category '{name}': {err}")

    return by_name


def seed_courses(token, category_map, courses):
    existing = request("GET", "/courses?skip=0&limit=10000")
    existing_list = _normalize_collection(existing)
    existing_titles = {c.get("title", "").strip().lower() for c in existing_list if c.get("title")}
    total = min(COUNT, len(courses))
    for i, course_data in enumerate(courses[:total], start=1):
        title = course_data.get("title", f"Course {i}")
        if title.strip().lower() in existing_titles:
            if i % 10 == 0:
                print(f"[seed] skipped {i}/{total} (already exists)")
            continue
        description = course_data.get("description")
        category_name = course_data.get("category")
        level = course_data.get("level")
        price = course_data.get("price")
        sections = course_data.get("sections") or []

        category = category_map.get(category_name.lower()) if category_name else None

        payload = {
            "title": title,
            "description": description,
            "category_id": category.get("id") if category else None,
            "level": level,
            "price": price,
            "thumbnail_url": None,
        }

        course = request("POST", "/courses", token=token, data=payload)
        course_id = course["id"]

        for section in sections:
            section_title = section.get("title")
            if not section_title:
                continue
            try:
                created_section = request(
                    "POST",
                    f"/courses/{course_id}/sections",
                    token=token,
                    data={"title": section_title},
                )
            except Exception as err:
                print(f"[warn] cannot create section for {course_id}: {err}")
                continue

            section_id = created_section.get("id")
            for lesson in section.get("lessons", []):
                lesson_payload = {
                    "title": lesson.get("title"),
                    "content": lesson.get("content"),
                    "lesson_type": lesson.get("lesson_type"),
                    "duration": lesson.get("duration"),
                    "video_url": lesson.get("video_url"),
                }
                if not lesson_payload["title"]:
                    continue
                try:
                    request(
                        "POST",
                        f"/courses/{course_id}/sections/{section_id}/lessons",
                        token=token,
                        data=lesson_payload,
                    )
                except Exception as err:
                    print(f"[warn] cannot create lesson for {course_id}: {err}")

        if PUBLISH:
            try:
                request("PATCH", f"/courses/{course_id}/publish", token=token)
            except Exception as err:
                print(f"[warn] cannot publish {course_id}: {err}")

        if i % 10 == 0:
            print(f"[seed] created {i}/{total} courses")


def main():
    print(f"[seed] base_url={BASE_URL}")
    token = ensure_token()
    ensure_admin(token)
    print("[seed] authenticated")
    seed_data = load_seed_data()
    categories = seed_data.get("categories", [])
    courses = seed_data.get("courses", [])
    category_map = ensure_categories(token, categories)
    print(f"[seed] categories loaded: {len(category_map)}")
    seed_courses(token, category_map, courses)
    print("[seed] done")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"[error] {err}")
        sys.exit(1)
