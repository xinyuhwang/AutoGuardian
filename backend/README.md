# AutoGuardian backend

FastAPI service: API, auth, database, Claude calls, rules and jobs.

```bash
uv sync                          # install dependencies into .venv
uv run fastapi dev app/main.py   # http://localhost:8000  (docs at /docs)
uv run pytest                    # run tests
```

Environment variables:

| Name | Default | Purpose |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins allowed to call the API |
