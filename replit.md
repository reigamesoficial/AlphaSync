# AlphaSync

Multi-tenant SaaS platform for service businesses with WhatsApp chatbot integration. Includes a FastAPI backend and a React frontend panel.

## Architecture

### Backend (FastAPI + Python 3.12)
- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL (Replit-managed)
- **Auth**: JWT (access + refresh tokens via python-jose + passlib/bcrypt)
- **Pattern**: Repository → Service → Endpoint
- **Server**: Uvicorn (dev port 8000), Gunicorn (production)

### Frontend (React + TypeScript + Tailwind CSS)
- **Framework**: React 19 + Vite 6
- **Styling**: Tailwind CSS v3 (dark theme)
- **Router**: React Router v7
- **HTTP**: Axios with JWT interceptor
- **Dev server**: Vite on port 5000 (proxies `/api` → `localhost:8000`)

## Ports

| Service  | Port | URL                    |
|----------|------|------------------------|
| Frontend | 5000 | Webview (primary)      |
| Backend  | 8000 | API / console          |

## Project Structure

```
app/                        - FastAPI backend
├── api/v1/endpoints/       - REST endpoints
│   ├── auth.py             - Login + refresh
│   ├── clients.py          - Clients CRUD
│   ├── conversations.py    - Conversations + messages
│   ├── quotes.py           - Quotes + items
│   ├── dashboard.py        - Summary stats
│   ├── company.py          - Company settings
│   ├── companies.py        - Company + settings (legacy)
│   ├── users.py            - User profile
│   └── webhook.py          - WhatsApp webhook
├── core/                   - Config, security, tenancy
├── db/                     - Models, connection
├── repositories/           - DB access layer
├── schemas/                - Pydantic schemas
└── services/               - Business logic

frontend/                   - React panel
├── src/
│   ├── api/                - Axios API calls (auth, clients, conversations, quotes, company, dashboard)
│   ├── components/
│   │   ├── layout/         - AppLayout, Sidebar, Topbar
│   │   └── ui/             - Badge, StatCard, EmptyState, Spinner
│   ├── context/            - AuthContext (JWT + localStorage)
│   ├── pages/              - Login, Dashboard, Clients, Conversations, Quotes, Settings
│   ├── router/             - PrivateRoute
│   └── types/              - TypeScript interfaces
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

## Key Configuration

- `DATABASE_URL`: Replit PostgreSQL (auto-converted to psycopg2 format)
- `SECRET_KEY`: JWT signing key (set in userenv)
- `CORS_ORIGINS`: `["*"]` in dev (`.env`)
- `API_V1_PREFIX`: `/api/v1`

## Running (Development)

Both workflows start automatically:

```bash
# Backend API (port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend panel (port 5000)
cd frontend && npm run dev
```

## Seeding

```bash
python scripts/seed_admin.py
# Creates: company "AlphaSync", admin user admin@alphasync.app / changeme123
```

## API Docs

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Phase Progress

- [x] Phase 0: Infrastructure (CORS, startup logs, seed, .env.example)
- [x] Phase 1: REST API endpoints (clients, conversations, quotes, dashboard, company settings)
- [x] Phase 2 (partial): Frontend panel MVP (login, dashboard, clients, conversations, quotes, settings)
- [ ] Phase 2 (pending): PDF generation, appointments scheduling
- [ ] Phase 3: Admin multi-tenant management
- [ ] Phase 4: Alembic migrations, Gunicorn production config
- [ ] Phase 5: Advanced analytics, reporting

## Notes

- `PNAddressCatalog`, `PNAddressPlant`, etc. had duplicate index definitions — `index=True` on FK columns was removed to fix startup.
- `DATABASE_URL` from Replit uses `postgresql://` scheme; config auto-converts to `postgresql+psycopg2://`.
- `CORS_ORIGINS` env var is stored as plain string; `cors_origins_list` computed field parses it.
- Frontend Vite proxies all `/api/*` requests to the backend on port 8000.
