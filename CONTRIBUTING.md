# Contributing to Taskly API

Thanks for considering a contribution! This repo is a learning/portfolio project — issues and PRs are welcome.

## Getting set up

```bash
git clone https://github.com/Shivansh2904/taskly-api.git
cd taskly-api
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

## Running tests

```bash
pytest tests/ -v --cov=app
```

Tests use SQLite, so you don't need Postgres running.

## Running locally

```bash
uvicorn app.main:app --reload
# Swagger UI: http://localhost:8000/docs
```

Or with Docker:

```bash
docker compose up
```

## Database migrations

When you change a model in `app/models.py`, generate a migration:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## Style

- Type hints everywhere (this is Python 3.12, use `|` not `Optional[]`)
- Pydantic v2 for all request/response models
- Keep route handlers thin — push business logic into helpers or store-level methods
- New endpoints should:
  - Have a `response_model` declared
  - Include ownership checks via `_get_owned_project` or similar
  - Have at least one happy-path test and one error-path test

## Submitting a PR

1. Fork, branch, commit
2. Make sure `pytest` passes
3. Update README if you add an endpoint
4. Open the PR

## License

By contributing, you agree your contributions are licensed under MIT.
