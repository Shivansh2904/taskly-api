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
