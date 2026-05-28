# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Task sorting** — `?sort=created_at|due_date|title|priority` + `?order=asc|desc` on the task list; priority sorts by semantic rank (high > medium > low), not alphabetically
- **Task search** — `?search=` query param on `GET /projects/{id}/tasks` filters by case-insensitive title substring
- **Task comments** — `Comment` model with `POST`/`GET`/`DELETE` endpoints under `/projects/{id}/tasks/{tid}/comments`; only a comment's author may delete it (Alembic migration `003_add_comments.py`)
- `Makefile` with `install`, `dev`, `test`, `migrate`, `docker-up`, `clean` targets
- Render.com `render.yaml` deploy blueprint (API + free Postgres)
- GitHub issue and PR templates
- Weekly Dependabot updates for pip, GitHub Actions, and Docker
- `CONTRIBUTING.md` with development setup and PR guidelines

## [0.4.0] — 2026-05-27

### Added
- `GET /auth/me` returns the currently authenticated user
- `GET /projects/{id}/stats` returns task counts grouped by status, priority, and overdue
- `POST /projects/{id}/tasks/bulk` creates up to 100 tasks in one call
- `GET /projects/{id}/tasks/export` exports all tasks in a project as CSV
- `pyproject.toml` with pytest pythonpath configuration

### Fixed
- Pinned `bcrypt==4.0.1` for passlib 1.7.4 compatibility (newer bcrypt breaks passlib's bundled test)
- Auth tests now pass: `jti` UUID claim in refresh tokens prevents JWT collisions in fast SQLite tests
- Added `LoginRequest` schema so login does not apply the registration password-length validator
- Handle SQLite naive datetimes in the refresh token expiry comparison

## [0.3.0] — 2026-05-27

### Added
- `due_date` field on tasks (timezone-aware, nullable)
- `?overdue=true` query parameter on `GET /projects/{id}/tasks` filters to overdue tasks
- Alembic migration `002_add_due_date.py`
- 14-test `test_tasks.py` covering all task endpoints (create, list, filter, get, update, delete, ownership)

## [0.2.0] — 2026-05-27

### Changed
- **BREAKING**: Rewrote the entire stack from TypeScript/Fastify/Prisma to Python/FastAPI/SQLAlchemy 2/Alembic/pytest

### Added
- FastAPI + SQLAlchemy 2 with mapped column syntax
- Alembic migrations
- JWT auth with rotating refresh tokens (single-use)
- Pydantic v2 schemas with field-level validation
- pytest test suite using SQLite (no Postgres needed in CI)
- Docker Compose with Postgres 16
- GitHub Actions CI

## [0.1.0] — 2026-05-17

### Added
- Initial release as TypeScript/Fastify/Prisma project (subsequently rewritten in Python)
