# LedgerIQ — Backend

FastAPI + async SQLAlchemy + Alembic. PostgreSQL primary, SQLite fallback for
local dev.

## Prerequisites
- Python 3.11+
- (Recommended) `python3-venv` for an isolated environment:
  `sudo apt install python3.12-venv`

## Setup (standard — with a virtualenv)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # SQLite fallback works out of the box
alembic upgrade head            # create / migrate the database
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000 · Swagger docs: http://localhost:8000/docs

## Setup (no venv available — local deps dir)
If `python3 -m venv` fails because `python3-venv` isn't installed, install the
dependencies into a local folder and run with `PYTHONPATH`:
```bash
cd backend
pip install --target .deps -r requirements.txt
cp .env.example .env
PYTHONPATH=.deps:. python3 -m alembic upgrade head
PYTHONPATH=.deps:. python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration
All settings come from `.env` (see `.env.example`). Key ones:
- `DATABASE_URL` — leave empty for SQLite (`SQLITE_PATH`), or set a Postgres URL
  e.g. `postgresql://user:pass@localhost:5432/ledgeriq` (auto-upgraded to asyncpg).
- `JWT_SECRET` — set a long random string in production.
- `CORS_ORIGINS` — comma-separated; defaults allow the Vite dev server.
- `ENABLE_SCHEDULER` — `true`/`false` to toggle the APScheduler notification job.

## Database migrations
```bash
alembic upgrade head                          # apply migrations
alembic revision --autogenerate -m "message"  # create a new migration
alembic downgrade -1                           # roll back one
```
(Prefix with `PYTHONPATH=.deps:.` if using the no-venv setup.)

## Testing the API
- Interactive: open http://localhost:8000/docs, click **Authorize**, paste a
  JWT from `POST /api/v1/auth/login`, then exercise any endpoint.
- Health probe: `curl http://localhost:8000/health`
