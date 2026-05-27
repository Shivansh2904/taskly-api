# Taskly API

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.3-0A9EDC?style=flat&logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![CI](https://img.shields.io/github/actions/workflow/status/Shivansh2904/taskly-api/ci.yml?label=CI)

> REST API for a project and task management system — JWT auth with refresh token rotation, projects, tasks with status/priority filtering, and tag management. Built with FastAPI, SQLAlchemy 2, and PostgreSQL.

---

## What it does

Taskly is a backend API that lets users manage projects and tasks. You register, get a short-lived access token and a rotating refresh token, then create projects and fill them with tasks. Each task has a status (`todo`, `in_progress`, `done`), a priority (`low`, `medium`, `high`), and optional tags.

The main things it demonstrates:

- **JWT auth with refresh token rotation** — access tokens expire after 15 minutes; refresh tokens are single-use and rotated on every call, so a stolen token cannot be reused
- **SQLAlchemy 2 with mapped types** — uses the modern `Mapped[T]` / `mapped_column()` syntax instead of the older declarative style
- **Alembic migrations** — database schema is versioned; the initial migration creates all six tables
- **Pydantic v2 schemas** — request validation and response serialization are fully typed; the `UserCreate` validator enforces minimum password length at the schema level
- **Ownership checks** — every project and task read/write verifies the calling user owns the resource before touching the database
- **pytest with SQLite** — tests run against an in-memory SQLite database with no external dependencies, so CI works without a running Postgres instance

---

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async-compatible mapped columns) |
| Migrations | Alembic |
| Database | PostgreSQL 16 (SQLite for tests) |
| Auth | python-jose (HS256 JWT) + passlib bcrypt |
| Validation | Pydantic v2 |
| Tests | pytest + httpx TestClient |
| Container | Docker + docker-compose |

---

## API

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account, returns access + refresh token |
| `POST` | `/auth/login` | Login, returns access + refresh token |
| `POST` | `/auth/refresh` | Exchange refresh token for new token pair (old token is invalidated) |
| `GET` | `/auth/me` | Get the currently authenticated user |

### Projects

All project routes require `Authorization: Bearer <access_token>`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/projects` | List your projects (paginated) |
| `POST` | `/projects` | Create a project |
| `GET` | `/projects/{id}` | Get a project (includes task count) |
| `PATCH` | `/projects/{id}` | Update name or description |
| `DELETE` | `/projects/{id}` | Delete project and all its tasks |
| `GET` | `/projects/{id}/stats` | Get task counts grouped by status, priority, and overdue |

### Tasks

All task routes require the calling user to own the parent project.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/projects/{id}/tasks` | List tasks, filter by `?status=` or `?priority=` |
| `POST` | `/projects/{id}/tasks` | Create a task with optional tags |
| `POST` | `/projects/{id}/tasks/bulk` | Create up to 100 tasks in one call |
| `GET` | `/projects/{id}/tasks/export` | Export all tasks as CSV |
| `GET` | `/projects/{id}/tasks/{tid}` | Get a task |
| `PATCH` | `/projects/{id}/tasks/{tid}` | Update title, status, priority, tags |
| `DELETE` | `/projects/{id}/tasks/{tid}` | Delete a task |

---

## Running locally

**With Docker (recommended):**

```bash
git clone https://github.com/Shivansh2904/taskly-api.git
cd taskly-api
docker compose up
# API is available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

**Without Docker:**

```bash
# Requires Python 3.12+ and a running PostgreSQL instance
git clone https://github.com/Shivansh2904/taskly-api.git
cd taskly-api
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL, JWT_SECRET, JWT_REFRESH_SECRET
uvicorn app.main:app --reload
```

---

## Example usage

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "hunter2hunter2"}'

# Create a project
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Website relaunch", "description": "Q3 redesign"}'

# Add a task
curl -X POST http://localhost:8000/projects/1/tasks \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Update homepage copy", "priority": "high", "tags": ["content", "frontend"]}'

# List tasks filtered by status
curl "http://localhost:8000/projects/1/tasks?status=todo" \
  -H "Authorization: Bearer <access_token>"
```

---

## Running tests

Tests use SQLite so no database setup is needed:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

---

## Project structure

```
app/
  main.py          FastAPI app, middleware, router registration
  config.py        pydantic-settings env validation
  database.py      SQLAlchemy engine and session factory
  models.py        ORM models (User, Project, Task, Tag, RefreshToken)
  schemas.py       Pydantic request/response models
  auth.py          JWT encode/decode, bcrypt hashing
  routers/
    auth.py        /auth routes
    projects.py    /projects routes + get_current_user dependency
    tasks.py       /projects/{id}/tasks routes
alembic/
  env.py           Alembic migration runner
  versions/
    001_initial_schema.py   Creates all tables
tests/
  conftest.py      TestClient + SQLite database fixture
  test_auth.py     Auth endpoint tests
  test_projects.py Project endpoint tests
```

---

## License

MIT — Copyright (c) 2025 Shivansh Mishra
