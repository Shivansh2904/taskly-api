def test_register(client):
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate(client):
    client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert r.status_code == 409


def test_register_short_password(client):
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "short"})
    assert r.status_code == 422


def test_login(client):
    client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "test@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert r.status_code == 401


def test_refresh(client):
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    refresh_token = r.json()["refresh_token"]
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
    assert "refresh_token" in r2.json()


def test_refresh_token_rotation(client):
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    refresh_token = r.json()["refresh_token"]
    client.post("/auth/refresh", json={"refresh_token": refresh_token})
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 401
