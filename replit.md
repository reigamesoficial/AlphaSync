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
│   ├── api/                - Axios API calls (auth, clients, conversations, quotes, company, dashboard, measures)
│   ├── components/
│   │   ├── layout/         - AppLayout, AdminLayout, InstallerLayout, Sidebar, Topbar
│   │   └── ui/             - Badge, StatCard, EmptyState, Spinner
│   ├── context/            - AuthContext (JWT + localStorage)
│   ├── pages/              - Login, Dashboard, Clients, Conversations, Quotes, Settings, Measures, Schedule
│   │   ├── admin/          - AdminDashboard, AdminCompanies, AdminUsers, AdminMetrics, AdminSettings
│   │   └── installer/      - InstallerSchedule
│   ├── router/             - PrivateRoute (role-based guard)
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

## Roles & Access Control

| Role | Routes | Guard |
|------|--------|-------|
| `master_admin` | `/admin/*` | `require_master_admin` |
| `company_admin` | `/dashboard`, `/schedule`, etc. | `require_company_admin_or_master` |
| `seller` | `/dashboard`, `/schedule`, measures CRUD | `require_admin_seller_or_master` |
| `installer` | `/installer` | `require_installer` |

Master admin has `company_id = null` in JWT — cannot access tenant endpoints (403 from `get_tenant_company_id`).

## Chatbot Flow (protection_network domain)

1. Customer sends address → system looks up address in catalog
2. If multiple plants → bot asks customer to choose (plant name always shown)
3. Customer selects plant → system loads measures of that plant
4. `show_measures_to_customer = true` → bot shows measures list for customer to select
5. `show_measures_to_customer = false` → bot auto-selects all measures silently (plant name still shown)
6. → color selection → mesh type → automatic quote

## Phase Progress

- [x] Phase 0: Infrastructure (CORS, startup logs, seed, .env.example)
- [x] Phase 1: REST API endpoints (clients, conversations, quotes, dashboard, company settings)
- [x] Phase 2: Frontend panel (login, dashboard, clients, conversations, quotes, settings, measures, schedule)
- [x] Phase 3: Role/permission architecture (UserRole, PrivateRoute, role-based Sidebar, AdminLayout, InstallerLayout)
- [x] Phase 3: New endpoints (appointments CRUD, /admin/*, /installer/appointments, /measures CRUD)
- [x] Phase 3: Multi-tenancy security audit — all endpoints verified, company_id isolation confirmed
- [x] Phase 3: Chatbot plant→measure flow closed (plant name always visible, show_measures toggle respected)
- [x] Phase 3: Measures.tsx UX premium (fixed nested button bug, area totals per plant, stat cards)
- [x] Phase 3: Schedule.tsx rebuilt (stats, filter tabs, new appointment modal)
- [x] Phase 3: InstallerSchedule.tsx rebuilt (today/upcoming sections, status actions, expandable cards)
- [x] Phase 4: PDF generation (reportlab, GET /quotes/{id}/pdf, POST /quotes/{id}/generate-pdf, Quotes.tsx detail drawer with PDF download + status actions)
- [ ] Phase 4 remaining: Alembic migrations, Gunicorn production config
- [ ] Phase 5: Advanced analytics, reporting

## Notes

- `PNAddressCatalog`, `PNAddressPlant`, etc. had duplicate index definitions — `index=True` on FK columns was removed to fix startup.
- `DATABASE_URL` from Replit uses `postgresql://` scheme; config auto-converts to `postgresql+psycopg2://`.
- `CORS_ORIGINS` env var is stored as plain string; `cors_origins_list` computed field parses it.
- Frontend Vite proxies all `/api/*` requests to the backend on port 8000.
