import pytest


@pytest.fixture
def auth_headers(client):
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_project(client, auth_headers):
    r = client.post("/projects", json={"name": "My Project"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["name"] == "My Project"
    assert r.json()["task_count"] == 0


def test_list_projects_empty(client, auth_headers):
    r = client.get("/projects", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_list_projects(client, auth_headers):
    client.post("/projects", json={"name": "P1"}, headers=auth_headers)
    client.post("/projects", json={"name": "P2"}, headers=auth_headers)
    r = client.get("/projects", headers=auth_headers)
    assert r.json()["total"] == 2


def test_update_project(client, auth_headers):
    r = client.post("/projects", json={"name": "Old Name"}, headers=auth_headers)
    pid = r.json()["id"]
    r2 = client.patch(f"/projects/{pid}", json={"name": "New Name"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["name"] == "New Name"


def test_delete_project(client, auth_headers):
    r = client.post("/projects", json={"name": "To Delete"}, headers=auth_headers)
    pid = r.json()["id"]
    r2 = client.delete(f"/projects/{pid}", headers=auth_headers)
    assert r2.status_code == 204


def test_project_not_found(client, auth_headers):
    r = client.get("/projects/9999", headers=auth_headers)
    assert r.status_code == 404


def test_unauthorized_without_token(client):
    r = client.get("/projects")
    assert r.status_code == 403


def test_project_stats(client, auth_headers):
    r = client.post("/projects", json={"name": "Stats Project"}, headers=auth_headers)
    pid = r.json()["id"]

    client.post(
        f"/projects/{pid}/tasks",
        json={"title": "T1", "status": "todo", "priority": "low"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{pid}/tasks",
        json={"title": "T2", "status": "in_progress", "priority": "medium"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{pid}/tasks",
        json={"title": "T3", "status": "done", "priority": "high"},
        headers=auth_headers,
    )

    r2 = client.get(f"/projects/{pid}/stats", headers=auth_headers)
    assert r2.status_code == 200
    data = r2.json()
    assert data["project_id"] == pid
    assert data["project_name"] == "Stats Project"
    assert data["total_tasks"] == 3
    assert data["by_status"]["todo"] == 1
    assert data["by_status"]["in_progress"] == 1
    assert data["by_status"]["done"] == 1
    assert data["by_priority"]["low"] == 1
    assert data["by_priority"]["medium"] == 1
    assert data["by_priority"]["high"] == 1
    assert data["overdue"] == 0


def test_project_stats_unauthorized(client, auth_headers):
    r = client.post("/projects", json={"name": "Private"}, headers=auth_headers)
    pid = r.json()["id"]

    r2 = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    other_token = r2.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    r3 = client.get(f"/projects/{pid}/stats", headers=other_headers)
    assert r3.status_code == 404
