# AutoGuardian

Your personal AI vehicle health assistant.

AutoGuardian turns the paperwork from every dealer visit into a structured, permanent history of
your car, warns you **before** likely problems (aging battery, worn brakes, overdue fluids, open
recalls), and walks you through diagnosing issues step by step when something goes wrong, even
with no cell signal.

> **Status:** design phase. See the [design doc](docs/DESIGN.md). No code yet.
> First target vehicle: 2018 Honda Accord.

## Why

A traditional maintenance app says *"Oil change due in 3,000 miles."*
AutoGuardian should say:

> *Your 12V battery is about 3 years old and its last dealer test dropped from 78% to 65%.
> Get a load test before winter or your next long trip.*

The goal is to avoid being surprised by a breakdown in a parking garage at night, and to know
what to check and what to do when it happens anyway.

## Planned features

- **Document intelligence:** upload invoices and inspection reports (PDF or photo). The AI extracts
  mileage, services, measurements and recommendations, and you review the results before they're saved.
- **Vehicle memory:** an append-only timeline. Every measurement is linked to its source document.
- **Maintenance intelligence:** schedule rules per vehicle (including Honda Maintenance Minder
  codes), age- and season-aware alerts, and NHTSA recall checks by VIN.
- **AI mechanic:** a diagnostic chat that knows your car's history and separates confirmed
  findings from possible causes, recommended tests and safety warnings.
- **Emergency mode:** offline decision trees (won't start, dashboard dark, overheating, flashing
  check-engine, flat tire) plus a roadside-kit checklist.
- **Later:** trend forecasting, pre-trip check, repair-estimate explainer, cost tracking, and
  Bluetooth OBD-II through a native app.

## Principles

1. Evidence over guesses: every value shows its date and source, with no made-up health scores.
2. Deterministic rules for schedules and alerts; the LLM extracts, explains and asks questions.
3. History is never overwritten.
4. Prediction is not diagnosis: "approaching typical lifespan" means *inspect*, not *failing*.
5. Conservative safety guidance: brakes, steering, overheating and oil pressure mean stop safely and
   call for help.

## Planned stack

Decided: Next.js + Tailwind frontend, FastAPI backend, pnpm and uv, Postgres + SQLAlchemy. Other rows are proposals.

| Layer | Tech |
| --- | --- |
| Frontend | Next.js + TypeScript + Tailwind, installable PWA (`frontend/`) |
| Backend | Python FastAPI + Pydantic (`backend/`) |
| Database | PostgreSQL 17 (Docker) + SQLAlchemy 2.x (sync) + Alembic |
| AI | Claude API: document extraction and diagnostic chat |
| Data | NHTSA vPIC (VIN decode) and Recalls APIs |
| Notifications | Web Push |
| Later | Expo native app for Bluetooth OBD-II, using the same backend |

## Development

Requirements: Node 20.19+ or 22.12+ with pnpm, Python 3.13 with [uv](https://docs.astral.sh/uv/), and Docker.

```bash
# Database: Postgres 17 on localhost:5433
docker compose up -d --wait

# Backend: http://localhost:8000 (API docs at /docs)
cd backend && uv sync && uv run alembic upgrade head && uv run fastapi dev app/main.py

# Frontend: http://localhost:3000
cd frontend && pnpm install && pnpm dev
```

If you run the frontend on a port other than 3000, start the backend with
`CORS_ORIGINS=http://localhost:<port>` so the browser is allowed to call it.

Tests: `cd backend && uv run pytest` · Lint: `cd frontend && pnpm lint`

## Roadmap

| Phase | Scope |
| --- | --- |
| 1 | Add vehicle (VIN), upload → extract → review → timeline |
| 2 | Components, measurements, maintenance rules, alerts, recalls |
| 3 | Diagnostic chat with vehicle history |
| 4 | Offline emergency guides, PWA install, push notifications |
| 5 | Forecasting, pre-trip check, estimate explainer, cost tracking |
| 6 | Native app + BLE OBD-II |

Details are in [docs/DESIGN.md](docs/DESIGN.md).

## Disclaimer

AutoGuardian provides information, not professional repair advice. It cannot see everything about
your vehicle. When in doubt, especially with brakes, steering, overheating or warning lights, stop
safely and consult a qualified mechanic or roadside assistance.

## License

[Apache 2.0](LICENSE)
