# LedgerIQ

A production-ready **Personal Finance Management Platform** — track expenses, budgets,
goals, investments, subscriptions, EMIs and net worth in one place, with a data-driven
credit-card **cashback engine**, rule-based **AI insights**, and CSV/XLSX statement import.
Mobile-first, fully responsive, multi-user, and built around the Indian Rupee (₹).

> Inspired by the CRED / Fi / INDmoney experience.

---

## Table of contents

- [Architecture overview](#architecture-overview)
- [Tech stack](#tech-stack)
- [Project layout](#project-layout)
- [Run with Docker (recommended)](#run-with-docker-recommended)
- [Run locally for development](#run-locally-for-development)
- [Environment variables](#environment-variables)
- [Testing](#testing)
- [Phase summary](#phase-summary)

---

## Architecture overview

LedgerIQ is a clean, layered application split into an async API backend and a SPA frontend,
fronted by an nginx reverse proxy in production.

```
                         ┌──────────────────────────────────────────────┐
                         │                  nginx :80                    │
   Browser ───────────►  │  /api, /docs, /health  →  backend             │
                         │  /                     →  frontend (static)   │
                         └───────────────┬───────────────┬──────────────┘
                                         │               │
                          ┌──────────────▼──────┐   ┌────▼─────────────────┐
                          │  FastAPI backend     │   │  React SPA (static)  │
                          │  :8000               │   │  built by Vite       │
                          │                      │   └──────────────────────┘
                          │  routes → services   │
                          │       → models       │
                          └──────────┬───────────┘
                                     │  SQLAlchemy (async)
                          ┌──────────▼───────────┐
                          │  PostgreSQL :5432     │  (SQLite fallback in dev)
                          └──────────────────────┘
```

**Backend layering** (`backend/app/`):

| Layer        | Responsibility                                                       |
|--------------|----------------------------------------------------------------------|
| `api/routes` | HTTP endpoints, request/response wiring, status codes                |
| `schemas`    | Pydantic v2 request/response contracts (validation, serialization)   |
| `services`   | Business logic — cashback engine, categorizer, insights, importer    |
| `models`     | SQLAlchemy 2.0 ORM models (`Mapped`/`mapped_column`), portable enums  |
| `core`       | Settings, security (JWT + bcrypt), dependencies, scheduler           |
| `db`         | Async engine, session factory, declarative `Base`                    |
| `utils`      | Shared helpers                                                        |

**Frontend layering** (`frontend/src/`):

| Layer         | Responsibility                                             |
|---------------|-----------------------------------------------------------|
| `pages`       | Route-level screens (Dashboard, Analytics, modules)       |
| `components`  | Reusable UI + RHF-controlled form fields                  |
| `layouts`     | App shell / navigation                                    |
| `services`    | Axios client, generic CRUD service factories              |
| `hooks`       | React Query hooks (`createCrudHooks`)                     |
| `store`       | Zustand stores (auth, UI) with persistence                |
| `types`       | Shared TypeScript types (strict, no `any`)                |
| `routes`      | Router config + protected routes                          |

**Design principles:** clean architecture, SOLID, separation of concerns; all data is
user-scoped (multi-tenant by user); rule-based services (categorizer, insights) sit behind
abstract interfaces so they can be swapped for an LLM implementation later without touching
callers; enums are stored as portable `VARCHAR` so adding values needs no migration.

---

## Tech stack

**Frontend:** React 19 · TypeScript (strict) · Vite · MUI · React Query · React Hook Form ·
React Router v6 · Recharts · Framer Motion · Axios · Zustand

**Backend:** FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · JWT (access + refresh) ·
APScheduler · bcrypt

**Database:** PostgreSQL (primary) · SQLite (local fallback)

**Deployment:** Docker · Docker Compose · Nginx

---

## Project layout

```
LedgerIQ/
├── backend/
│   ├── app/                 # FastAPI application (routes, services, models, core, db)
│   ├── alembic/             # async migrations
│   ├── tests/               # pytest suite (cashback engine + auth flow)
│   ├── Dockerfile
│   ├── docker-entrypoint.sh # runs `alembic upgrade head` then starts uvicorn
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/                 # React + TypeScript SPA
│   ├── Dockerfile           # multi-stage: vite build → nginx static serve
│   └── nginx.conf           # SPA fallback config (inside the frontend image)
├── nginx/
│   └── nginx.conf           # production reverse proxy (api + spa)
├── docker-compose.yml       # postgres + backend + frontend + nginx
├── .env.example             # compose-level secrets/config
└── README.md
```

---

## Run with Docker (recommended)

Requires Docker + Docker Compose.

```bash
# 1. Configure secrets
cp .env.example .env
# edit .env — set POSTGRES_PASSWORD and a strong JWT_SECRET
#   python -c "import secrets; print(secrets.token_urlsafe(48))"

# 2. Build and start the whole stack
docker compose up --build -d

# 3. Open the app
#    App / UI ........ http://localhost
#    API docs ........ http://localhost/docs
#    Health check .... http://localhost/health
```

On startup the backend automatically runs `alembic upgrade head` against PostgreSQL before
serving. To change the public port, set `HTTP_PORT` in `.env` (e.g. `HTTP_PORT=8080`).

```bash
docker compose logs -f         # tail logs
docker compose down            # stop (keeps the pgdata volume)
docker compose down -v         # stop and wipe the database volume
```

---

## Run locally for development

Run the backend and frontend in two terminals. No Docker required; the backend falls back
to a local SQLite file when `DATABASE_URL` is empty.

### Backend (FastAPI · http://localhost:8000)

```bash
cd backend
cp .env.example .env                       # DATABASE_URL empty → SQLite fallback

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head                       # create the schema
uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000/api/v1`
- Interactive docs: `http://localhost:8000/docs`

### Frontend (Vite · http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies API calls to the backend on `:8000` and CORS is pre-configured for
`http://localhost:5173`. Useful scripts:

```bash
npm run build       # type-check (tsc --noEmit) + production build
npm run typecheck   # type-check only
npm run preview     # serve the production build locally
```

---

## Environment variables

### Compose (`.env` at the repo root)

| Variable            | Description                                  | Example                       |
|---------------------|----------------------------------------------|-------------------------------|
| `POSTGRES_USER`     | Postgres username                            | `ledgeriq`                    |
| `POSTGRES_PASSWORD` | Postgres password                            | `change_this_password`        |
| `POSTGRES_DB`       | Postgres database name                       | `ledgeriq`                    |
| `JWT_SECRET`        | Secret for signing JWTs (use a long random)  | `…token_urlsafe(48)…`         |
| `PUBLIC_ORIGIN`     | Public origin, used for CORS                  | `http://localhost`            |
| `HTTP_PORT`         | Host port the nginx proxy listens on         | `80`                          |

### Backend (`backend/.env`)

| Variable                      | Description                                                        | Default                |
|-------------------------------|-------------------------------------------------------------------|------------------------|
| `ENVIRONMENT`                 | `local` \| `development` \| `staging` \| `production`             | `local`                |
| `DEBUG`                       | Verbose errors; surfaces reset token in responses for testing      | `true`                 |
| `API_V1_PREFIX`               | API route prefix                                                   | `/api/v1`              |
| `CORS_ORIGINS`                | Comma-separated allowed origins                                   | `http://localhost:5173`|
| `DATABASE_URL`                | Postgres URL (sync-style; upgraded to asyncpg). Empty → SQLite    | _empty_                |
| `SQLITE_PATH`                 | SQLite file used when `DATABASE_URL` is empty                     | `./ledgeriq.db`        |
| `JWT_SECRET`                  | JWT signing secret                                                | _change me_            |
| `JWT_ALGORITHM`               | JWT algorithm                                                     | `HS256`                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime                                            | `30`                   |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh-token lifetime                                            | `7`                    |
| `ENABLE_SCHEDULER`            | Run APScheduler notification jobs                                | `true` (prod)          |
| `DEFAULT_CURRENCY`            | Default currency                                                  | `INR`                  |
| `DEFAULT_LOCALE`              | Default locale                                                    | `en-IN`                |
| `DEFAULT_TIMEZONE`            | Default timezone                                                  | `Asia/Kolkata`         |

> Never commit a real `.env`. Both `.env` files are git-ignored; only the `.env.example`
> templates are tracked.

---

## Testing

The backend ships with example unit/integration tests (cashback engine + auth flow):

```bash
cd backend
pip install -r requirements.txt        # includes pytest + pytest-asyncio
pytest -q
```

Tests run against a throwaway SQLite database and the scheduler is disabled, so they need no
external services. Coverage includes:

- **Cashback engine** — rule matching by card, the Swiggy ≥ ₹249 qualification threshold,
  the SBI 5% online cashback ₹2000/month cap, and the no-card case.
- **Auth flow** — register → login → profile, duplicate-email conflict, weak-password
  rejection, wrong-password/no-token rejection, and refresh-token rotation.

---

## Phase summary

LedgerIQ was built in deliberate phases, each self-contained and verified before moving on:

| Phase | Focus                                                                                          |
|-------|------------------------------------------------------------------------------------------------|
| **1** | Backend architecture & database — async SQLAlchemy models, portable enums, Alembic setup       |
| **2** | Authentication — JWT access/refresh, bcrypt hashing, register/login/profile/refresh routes      |
| **3** | Expense management — cashback engine (data-driven rules + caps) and rule-based AI categorizer   |
| **4** | Remaining domains — income, credit cards, budgets (Green/Yellow/Red), goals, investments, subscriptions, EMIs, net worth, and scheduled notifications |
| **5** | Frontend shell — theme, routing, app layout, navigation, auth screens                           |
| **6** | Dashboard & analytics — KPIs, Recharts visualisations, summary widgets                          |
| **7** | AI insights & module screens — per-domain CRUD UIs and CSV/XLSX statement import with auto-mapping |
| **8** | Deployment & tests — Dockerfiles, docker-compose, nginx reverse proxy, this README, unit tests  |

---

Built with FastAPI + React. All amounts are in Indian Rupees (₹).
