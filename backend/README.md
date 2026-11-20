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
| `UPLOAD_DIR` | `uploads` (inside `backend/`, git-ignored) | Where uploaded documents are stored |
| `MAX_UPLOAD_MB` | `20` | Maximum size per uploaded file |
| `SESSION_COOKIE_SECURE` | `false` | Set `true` in production so the session cookie is HTTPS-only |
| `SESSION_LIFETIME_DAYS` | `30` | How long a login lasts |

## Auth

Email + password. `POST /auth/register` / `POST /auth/login` set an HTTP-only `ag_session`
cookie; `POST /auth/logout` deletes it; `GET /auth/me` returns the current user. Only a SHA-256
hash of the session token is stored. Protected endpoints take `user: CurrentUser` and must filter
every query by `user.id`; another user's records return 404.

## VIN decoding

`GET /vehicles/decode-vin?vin=...` validates the VIN (17 chars, no I/O/Q, check digit), asks NHTSA
vPIC (free, no key) and returns *proposed* details plus warnings. It never saves; the frontend
saves with `POST /vehicles` after the user confirms. Logic is in `app/vin.py`; tests mock NHTSA via
the `get_http_client` dependency, so they never touch the network. The frontend must call the API with
`credentials: "include"`.

## Documents

- `POST /vehicles/{id}/documents` (multipart, field `files`, repeatable; optional `note`): one
  document made of 1–20 files (pages). Types are detected from file contents: PDF, JPEG, PNG, HEIC.
  HEIC is converted to JPEG (EXIF rotation applied) and the original is kept too. The whole upload
  is rejected if any file is invalid.
- `GET /vehicles/{id}/documents`: newest first, with files.
- `GET /documents/{doc}/files/{file}[?original=true]`: view a file (inline).
- Files are stored as `UPLOAD_DIR/vehicles/<vehicle>/documents/<document>/<random>.<ext>`; user
  filenames are never used in paths. Storage lives behind `app/storage.py` so it can move to
  S3-compatible storage later.
