import pytest


@pytest.fixture
def auth_headers(client):
    r = client.post("/auth/register", json={"email": "taskuser@example.com", "password": "password123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project_id(client, auth_headers):
    r = client.post("/projects", json={"name": "Test Project"}, headers=auth_headers)
    return r.json()["id"]


def _task_url(project_id, task_id=None):
    base = f"/projects/{project_id}/tasks"
    return base if task_id is None else f"{base}/{task_id}"


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_task(client, auth_headers, project_id):
    r = client.post(
        _task_url(project_id),
        json={"title": "My Task", "description": "Some details"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "My Task"
    assert data["description"] == "Some details"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["project_id"] == project_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "due_date" in data


def test_create_task_with_due_date(client, auth_headers, project_id):
    r = client.post(
        _task_url(project_id),
        json={"title": "Dated Task", "due_date": "2030-01-15T12:00:00"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Dated Task"
    assert data["due_date"] is not None
    assert "2030-01-15" in data["due_date"]


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_tasks_empty(client, auth_headers, project_id):
    r = client.get(_task_url(project_id), headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_list_tasks_returns_list(client, auth_headers, project_id):
    client.post(_task_url(project_id), json={"title": "T1"}, headers=auth_headers)
    client.post(_task_url(project_id), json={"title": "T2"}, headers=auth_headers)
    r = client.get(_task_url(project_id), headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_tasks_by_status(client, auth_headers, project_id):
    r1 = client.post(_task_url(project_id), json={"title": "Todo task", "status": "todo"}, headers=auth_headers)
    r2 = client.post(_task_url(project_id), json={"title": "Done task", "status": "done"}, headers=auth_headers)
    assert r1.status_code == 201
    assert r2.status_code == 201

    r = client.get(_task_url(project_id), params={"status": "todo"}, headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert all(t["status"] == "todo" for t in items)
    assert len(items) == 1
    assert items[0]["title"] == "Todo task"


def test_filter_tasks_by_priority(client, auth_headers, project_id):
    client.post(_task_url(project_id), json={"title": "Low P", "priority": "low"}, headers=auth_headers)
    client.post(_task_url(project_id), json={"title": "High P", "priority": "high"}, headers=auth_headers)

    r = client.get(_task_url(project_id), params={"priority": "high"}, headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["title"] == "High P"
    assert items[0]["priority"] == "high"


# ── Get single ────────────────────────────────────────────────────────────────

def test_get_task(client, auth_headers, project_id):
    create_r = client.post(
        _task_url(project_id), json={"title": "Fetch Me"}, headers=auth_headers
    )
    tid = create_r.json()["id"]

    r = client.get(_task_url(project_id, tid), headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == tid
    assert r.json()["title"] == "Fetch Me"


def test_get_nonexistent_task(client, auth_headers, project_id):
    r = client.get(_task_url(project_id, 99999), headers=auth_headers)
    assert r.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_task_title(client, auth_headers, project_id):
    create_r = client.post(
        _task_url(project_id), json={"title": "Old Title"}, headers=auth_headers
    )
    tid = create_r.json()["id"]

    r = client.patch(_task_url(project_id, tid), json={"title": "New Title"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "New Title"


def test_update_task_status_to_done(client, auth_headers, project_id):
    create_r = client.post(
        _task_url(project_id), json={"title": "Work Item"}, headers=auth_headers
    )
    tid = create_r.json()["id"]
    assert create_r.json()["status"] == "todo"

    r = client.patch(_task_url(project_id, tid), json={"status": "done"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "done"


def test_update_task_tags(client, auth_headers, project_id):
    create_r = client.post(
        _task_url(project_id), json={"title": "Taggable"}, headers=auth_headers
    )
    tid = create_r.json()["id"]

    r = client.patch(
        _task_url(project_id, tid),
        json={"tags": ["backend", "urgent"]},
        headers=auth_headers,
    )
    assert r.status_code == 200
    tag_names = {t["name"] for t in r.json()["tags"]}
    assert tag_names == {"backend", "urgent"}


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_task(client, auth_headers, project_id):
    create_r = client.post(
        _task_url(project_id), json={"title": "To Delete"}, headers=auth_headers
    )
    tid = create_r.json()["id"]

    r = client.delete(_task_url(project_id, tid), headers=auth_headers)
    assert r.status_code == 204

    # Confirm it's gone
    r2 = client.get(_task_url(project_id, tid), headers=auth_headers)
    assert r2.status_code == 404


# ── Cross-user isolation ──────────────────────────────────────────────────────

def test_cannot_access_task_in_another_users_project(client, auth_headers, project_id):
    """A second user should not be able to see tasks in the first user's project."""
    create_r = client.post(
        _task_url(project_id), json={"title": "Private Task"}, headers=auth_headers
    )
    tid = create_r.json()["id"]

    # Register and log in a second user
    r2 = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    other_token = r2.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # The other user tries to read the task — should 404 (project not owned)
    r = client.get(_task_url(project_id, tid), headers=other_headers)
    assert r.status_code == 404


# ── Overdue filter ────────────────────────────────────────────────────────────

def test_overdue_filter_returns_past_due_tasks(client, auth_headers, project_id):
    # Past due, not done — should appear in overdue
    client.post(
        _task_url(project_id),
        json={"title": "Overdue Task", "due_date": "2000-01-01T00:00:00", "status": "todo"},
        headers=auth_headers,
    )
    # Future due — should NOT appear
    client.post(
        _task_url(project_id),
        json={"title": "Future Task", "due_date": "2099-12-31T00:00:00"},
        headers=auth_headers,
    )
    # Past due but done — should NOT appear
    client.post(
        _task_url(project_id),
        json={"title": "Done Overdue", "due_date": "2000-01-01T00:00:00", "status": "done"},
        headers=auth_headers,
    )

    r = client.get(_task_url(project_id), params={"overdue": "true"}, headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["title"] == "Overdue Task"
