# AutoGuardian backend

FastAPI service: API, auth, database, Claude calls, rules and jobs.
SQLAlchemy 2.x (sync) + Alembic on PostgreSQL 17.

```bash
docker compose up -d --wait      # from the repo root: Postgres on localhost:5433
uv sync                          # install dependencies into .venv
uv run alembic upgrade head      # create/update tables in the dev database
uv run fastapi dev app/main.py   # http://localhost:8000  (docs at /docs)
uv run pytest                    # run tests (uses the separate autoguardian_test database)
```

## Layout

```text
app/
  main.py       FastAPI app, CORS, routes
  config.py     settings from environment variables
  db.py         engine, session, Base, TimestampMixin, get_db dependency
  models/       one file per table; import all via app.models
  auth/         passwords (argon2), sessions, /auth routes, CurrentUser dependency
  routers/      feature endpoints (vehicles, ...); always filter by CurrentUser
alembic/        migrations (versions/ holds one file per schema change)
tests/          pytest; conftest.py builds the test DB from migrations
```

## Changing the schema

1. Edit or add a model in `app/models/` (and export it from `app/models/__init__.py`).
2. `uv run alembic revision --autogenerate -m "short description"`
3. Read the generated file in `alembic/versions/` and fix anything autogenerate missed.
4. `uv run alembic upgrade head`, then `uv run pytest`.

## Environment variables

| Name | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://autoguardian:autoguardian@localhost:5433/autoguardian` | Dev database |
| `TEST_DATABASE_URL` | same server, database `autoguardian_test` | Test database (wiped by each test run) |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins allowed to call the API |
| `SESSION_COOKIE_SECURE` | `false` | Set `true` in production so the session cookie is HTTPS-only |
| `SESSION_LIFETIME_DAYS` | `30` | How long a login lasts |

## Auth

Email + password. `POST /auth/register` / `POST /auth/login` set an HTTP-only `ag_session`
cookie; `POST /auth/logout` deletes it; `GET /auth/me` returns the current user. Only a SHA-256
hash of the session token is stored. Protected endpoints take `user: CurrentUser` and must filter
every query by `user.id`; another user's records return 404. The frontend must call the API with
`credentials: "include"`.
