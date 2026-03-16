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
│   ├── api/                - Axios API calls (auth, clients, conversations, quotes, company, dashboard, measures, admin)
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
- [x] Phase 4 (Parte 3 SaaS): Onboarding service + AdminCompanies rebuild
  - `app/services/onboarding_service.py` — atomic bootstrap (company + settings + admin) with domain defaults for protection_network
  - `app/schemas/company.py` — added CompanyCreateFull, CompanyListItem, CompanyDetailResponse, AdminUserSummary, BootstrapAdminPayload
  - `app/api/v1/endpoints/admin.py` — rewritten: GET /admin/companies (paginated), GET /admin/companies/{id}, POST /admin/companies (full bootstrap), PATCH /admin/companies/{id}, POST /admin/companies/{id}/bootstrap-admin
  - `frontend/src/api/admin.ts` — new admin API client (listCompanies, getCompany, createCompany, updateCompany, bootstrapAdmin)
  - `frontend/src/pages/admin/AdminCompanies.tsx` — rebuilt: stats cards, paginated table with search, detail drawer (settings/admin status, config info, plan edit, toggle active), create modal (full company + admin form, auto-slug), bootstrap-admin form
- [x] Phase 4 (Parte 3 SaaS): Platform Settings + Users full CRUD
  - `app/db/models.py` — added PlatformSettings (singleton, id=1, auto-created on first GET)
  - `app/schemas/platform_settings.py` — PlatformSettingsBase, PlatformSettingsUpdate, PlatformSettingsResponse
  - `app/schemas/users.py` — added AdminUserResponse (with company_name/slug), AdminUserUpdate (with company_id)
  - `app/api/v1/endpoints/admin.py` — added: GET/PATCH /admin/settings, GET /admin/users/{id}, PATCH /admin/users/{id}; enhanced GET /admin/users (paginated, with company_name, role/search/company/is_active filters)
  - `frontend/src/api/admin.ts` — added: getPlatformSettings, updatePlatformSettings, listUsers, getUser, createUser, updateUser + full TypeScript types
  - `frontend/src/pages/admin/AdminSettings.tsx` — rebuilt: form with 3 sections (Plataforma, Padrões, Suporte), toggle allow_self_signup, live dirty state, save button
  - `frontend/src/pages/admin/AdminUsers.tsx` — rebuilt: paginated table with search/role/company filters, right-side edit drawer (name/email/role/company/is_active), password reset, create modal, activate/deactivate action
- [x] Phase 4 (Parte 4 SaaS): Company user management for COMPANY_ADMIN
  - `app/api/v1/endpoints/company.py` — added: GET/POST/GET/{id}/PATCH/{id} for /company/users
    - Always scoped by JWT company_id (get_tenant_company_id); cannot create master_admin; roles allowed: company_admin, seller, installer, viewer
  - `frontend/src/api/companyUsers.ts` — new API client (listCompanyUsers, getCompanyUser, createCompanyUser, updateCompanyUser)
  - `frontend/src/pages/CompanyUsers.tsx` — new page: paginated table with search/role/status filters, right-side drawer (edit name/email/role, password reset, activate/deactivate), create modal
  - `frontend/src/components/layout/Sidebar.tsx` — added "Usuários" menu item (UserCog icon, /company-users route) only in adminNav (company_admin); sellerNav unchanged; also added logout button
  - `frontend/src/App.tsx` — added /company-users route under PrivateRoute allowedRoles=['company_admin']
- [x] Phase 4 (Parte 4 produção): Hardening, deploy e infraestrutura
  - **Alembic**: `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/README`; baseline migration `daa5034677ed` gerado com `--autogenerate` e DB marcado com `alembic stamp head`
  - **Gunicorn**: `gunicorn==23.0.0` adicionado ao `requirements.txt`; `gunicorn.conf.py` com UvicornWorkers, max_requests, graceful_timeout, configuração via env vars
  - **Redis**: `app/core/redis_client.py` com pool de conexões, `redis_health()`, helpers `cache_get/set/delete`
  - **Healthchecks**: `GET /health` (básico) e `GET /health/full` (DB + Redis, retorna 207 se degraded)
  - **Logging**: `_JsonFormatter` para produção (JSON estruturado); texto legível para desenvolvimento; request-id middleware
  - **Dockerfile**: multi-stage build (builder + runtime), usuário não-root, HEALTHCHECK nativo, CMD usa gunicorn
  - **frontend/Dockerfile**: build Vite em node:20-alpine, serve estático com nginx; suporta React Router (try_files)
  - **docker-compose.yml**: 6 serviços (postgres, redis, backend, frontend, nginx, migrations); healthchecks em todos; profiles para migrations; volumes nomeados
  - **nginx/nginx.conf**: reverse proxy com rate limiting (api: 60r/m, auth: 10r/m), headers de segurança, SSL comentado pronto para ativar
  - **DEPLOY.md**: guia completo de deploy em VPS (setup, first deploy, SSL, backups, atualizações, checklist de 15 itens)
- [ ] Phase 5: Advanced analytics, reporting

## Notes

- `PNAddressCatalog`, `PNAddressPlant`, etc. had duplicate index definitions — `index=True` on FK columns was removed to fix startup.
- `DATABASE_URL` from Replit uses `postgresql://` scheme; config auto-converts to `postgresql+psycopg2://`.
- `CORS_ORIGINS` env var is stored as plain string; `cors_origins_list` computed field parses it.
- Frontend Vite proxies all `/api/*` requests to the backend on port 8000.
