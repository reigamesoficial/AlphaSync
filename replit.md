# AlphaSync

Multi-tenant SaaS platform for service businesses with WhatsApp chatbot integration. Includes a FastAPI backend and a React frontend panel.

## Frontend Evolution (2026-03-17) — Premium Redesign + New Pages

### Theme System
- **`frontend/src/context/ThemeContext.tsx`** (NEW): `ThemeProvider` + `useTheme()` hook with localStorage persistence
- `main.tsx` wrapped with `ThemeProvider`
- **`frontend/src/index.css`**: CSS `[data-theme="light"]` overrides for all surface, border, text, input, card, and button classes
- **`frontend/tailwind.config.js`**: darkMode updated to `['class', '[data-theme="dark"]']` for attribute-based switching

### Layout Revamp
- **`frontend/src/components/layout/Sidebar.tsx`**: Full redesign
  - Sectioned navigation (Operacional / Análise / Campo / Gestão)
  - Active state with brand-colored border + dot indicator
  - Theme toggle (animated pill switch) with Sun/Moon icon
  - User avatar with role-colored status dot + logout button (LogOut icon)
  - New nav items: Financeiro (BarChart3) and CRM / Funil (GitBranch)
- **`frontend/src/components/layout/Topbar.tsx`**: Premium redesign
  - Optional `breadcrumb` prop for hierarchical context
  - Optional `action` prop for page-level action buttons
  - Notification bell with indicator dot
  - User avatar chip (no duplicate logout — now in Sidebar)

### New Pages
- **`frontend/src/pages/Financial.tsx`** (NEW): `/financial` route
  - 4 KPI cards: Receita Total, Orçamentos Confirmados, Clientes Ativos, Taxa de Conversão
  - Area chart: Receita Mensal (recharts, last 6 or 12 months toggle)
  - Bar chart: Orçamentos / Mês
  - Top Clients table with proportional progress bars
  - Loads from `GET /api/v1/dashboard/financial?months=6`
- **`frontend/src/pages/CRM.tsx`** (NEW): `/crm` route
  - Kanban board with 6 pipeline stages: Lead → Contactado → Visita Agendada → Orçamento Enviado → Ganho → Perdido
  - Stage summary bar with live counts and conversion rate
  - Client cards with avatar, phone, role/seller attribution
  - Search filter, refresh button
  - Stage mapped from client `status` field
  - Quick action links at bottom

### Backend — Financial Endpoint
- **`app/api/v1/endpoints/dashboard.py`**: Added `GET /dashboard/financial`
  - `months` query param (1–24, default 6)
  - Revenue (CONFIRMED + DONE quotes), monthly breakdown, top clients
  - Conversion rate: (confirmed + done) / total quotes × 100
  - All queries scoped per `company_id` (multi-tenant safe)
  - Date math with pure Python (no external libs)

### Packages
- `recharts` added to frontend dependencies

## Recent Features (2026-03-17) — Global Menu Layer

### Global Bot Menu + Full Flow Layer (all 8 domains)
- **`app/domains/_shared/global_menu.py`** (NEW): Global menu intercepted before any domain flow
  - 5-option list message: Solicitar orçamento / Agendar visita técnica / Tenho orçamento / Reagendar serviço / Cancelar agendamento
  - Step handlers: `global_main_menu`, `global_tech_visit_*`, `global_has_quote_*`, `global_reschedule_*`, `global_cancel_*`, `global_done`
  - Schedule utilities: `_get_schedule_cfg()`, `_compute_slots()`, `_compute_available_days()` (shared, independent of domain)
  - Creates `Appointment` rows for: tech visit scheduling, "has quote" scheduling, and reschedule
  - Cancels existing appointment on reschedule/cancel flows

- **`app/services/conversation_service.py`** MODIFIED:
  - `_execute_domain_flow()` now injects global menu layer BEFORE calling domain flow
  - Global reset: any word in `RESET_WORDS` clears `global_menu_done` flag and shows menu again
  - `_call_domain_chatbot()` extracted as standalone helper (called by both layer and domain_caller callback)
  - `_send_domain_response()` now handles `action == "assumed"` — sends text to client via WhatsApp before pausing bot

- **`app/domains/protection_network/chatbot_flow.py`** MODIFIED (Etapa 4):
  - When address not found in catalog: instead of immediately ASSUMED, asks "Você já tem as medidas?"
  - New step `ask_has_measures`: Sim → `manual_measurements` + disclaimer warning | Não → ASSUMED/human handoff

- **`app/db/models.py`** MODIFIED:
  - `ReminderStatus` enum: added `SKIPPED = "skipped"` and `FAILED = "failed"` (were missing, caused `AttributeError`)

- **`app/services/reminder_service.py`** FIXED (3 bugs):
  1. `update_appointment(appointment.id, ...)` → `update_appointment(appointment, ...)` (was passing int, not object)
  2. `company_id=` keyword arg removed (doesn't exist in signature)
  3. `ReminderStatus.SKIPPED/FAILED` were undefined — now fixed by models.py change
  4. Added `_send_reminder_message()` with template fallback for closed 24h Meta window

- **`app/services/whatsapp_service.py`** MODIFIED:
  - Added `send_template_message()` for HSM templates (used for outbound reminders outside 24h window)

- **`app/api/v1/endpoints/conversations.py`** MODIFIED (2 new endpoints, now 86 total):
  - `POST /conversations/{id}/tech-visit-confirm`: Seller says "Precisa de visita" → sends day list to client, sets step to `global_tech_visit_schedule_day`
  - `POST /conversations/{id}/tech-visit-to-quote`: Seller says "Seguir orçamento" → sets `global_menu_done=True`, starts domain quote flow

- **`frontend/src/api/conversations.ts`** MODIFIED:
  - Added `techVisitConfirm()` and `techVisitToQuote()` API calls

- **`frontend/src/pages/Conversations.tsx`** MODIFIED:
  - Added state `techVisitAction` + handlers `handleTechVisitConfirm()`, `handleTechVisitToQuote()`
  - Added two seller action buttons in ChatDrawer footer, visible when `conv.bot_step === 'global_tech_visit_waiting'`

- **Migration `c978f46cdd18`**: `ALTER TYPE reminder_status_enum ADD VALUE 'skipped'/'failed'`

### 24h Meta Window — Diagnosis + Solution
- **Affected**: `reminder_service.py` sends proactively (outside window possible) → now has template fallback
- **Not affected**: appointment confirmation (client just replied → window open), return-to-bot (triggered by seller after client interaction)
- **Production**: set `reminder_template_name` in `company.extra_settings` for guaranteed delivery

## Recent Features (2026-03-17) — 3 Operational Fronts — VPS Pre-Deploy
**Frente 1 — Bot: Agendamento após confirmação de orçamento**
- Chatbot flow (`chatbot_flow.py`) extended with scheduling steps after quote confirmation
- New steps: `schedule_ask` → `schedule_date` → `schedule_slot` → `schedule_confirmed`
- `_get_schedule_cfg()`: reads slot config from company settings
- `_compute_slots()`: generates available time slots for a given date
- `_parse_date_br()`: parses DD/MM and DD/MM/YYYY date formats
- `_format_date_pt()`: formats date in Portuguese (e.g., "18/03/2026 (quarta-feira)")
- Creates `Appointment` in DB (linked to quote, client, address) via `AppointmentsRepository`

**Frente 2 — Botão "Gerar Orçamento" no painel do vendedor**
- Backend: `POST /conversations/{id}/generate-quote` with 2 modes:
  - Mode `m2`: items with description/width/height/qty + color + mesh → uses pricing rules
  - Mode `manual`: description + fixed value → direct quote creation
- Backend: `GET /company/profile` — returns `service_domain` + basic company info
- Frontend: `QuoteModal` component with 2 tabs ("Calcular m²" / "Valor fixo")
- Frontend: "Gerar Orçamento" button in `ChatDrawer` footer — visible **only** for `protection_network` companies
- Toast notification shows quote ID and total value on success
- `service_domain` loaded at `Conversations` page mount via `getCompanyProfile()`

**Frente 3 — Horários de serviço** ✅ Already complete (Settings tab "Agendamento")

### Scheduling Business Rules
- **Past-date blocking**: `POST/PATCH /appointments` now rejects dates in the past (422 error)
- **Installer conflict detection**: Detects overlapping active appointments for the same installer (409 error)
- **Configurable time slots**: `GET /appointments/slots?date=YYYY-MM-DD&installer_id=X` returns available/busy slots
- **Company schedule config**: `GET/PATCH /company/schedule-config` (slot_minutes, workday_start/end, allowed_weekdays) stored in `CompanySettings.extra_settings.schedule`
- **Installer availability**: `GET /company/installers` + `PATCH /company/installers/{id}/schedule` — per-installer work hours/days stored in `CompanySettings.extra_settings.installer_schedules`

### Bot Flow Message Configuration
- `GET/PATCH /company/flow-config` — editable greeting/fallback/tone per domain (all 8)
- Stored in `CompanySettings.extra_settings.{domain_key}.bot_messages`
- Falls back to `DomainDefinition.config_json` defaults when no company override

### Frontend Updates
- **Schedule.tsx**: Slot picker (replaces raw datetime inputs), past-date `min` restriction, installer selector, conflict error passthrough
- **Settings.tsx**: 2 new tabs — "Agendamento" (slot config + per-installer availability), "Fluxo do Bot" (domain-specific bot messages with expandable cards)

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
- [x] Phase 7: DomainDefinition model + CRUD API + frontend `/admin/domains`
  - **Model** (`app/db/models.py`): `DomainDefinition` table (key, display_name, description, icon, is_active, is_builtin, config_json JSON)
  - **Repository** (`app/repositories/domain_definitions.py`): `DomainDefinitionsRepository` extends `BaseRepository`
  - **Schema** (`app/schemas/domain_definitions.py`): `DomainDefinitionResponse`, `DomainDefinitionListItem`, `DomainDefinitionUpdate`, `DomainSyncResult`
  - **Service** (`app/services/domain_definition_service.py`): `sync_builtin_domains()`, CRUD, `get_onboarding_config(key)`; full `config_json` defaults per domain (bot messages, services list, pricing defaults, onboarding defaults, labels)
  - **API** (`app/api/v1/endpoints/domain_definitions.py`): 4 endpoints under `/admin/domains` (GET list, GET by key, PUT update, POST sync) — all require MASTER_ADMIN
  - **Startup sync** (`app/main.py`): auto-seeds all 8 builtin domains on startup; idempotent (skips existing)
  - **Onboarding integration** (`app/services/onboarding_service.py`): `bootstrap_company()` now uses `DomainDefinitionService.get_onboarding_config()` with fallback to static defaults
  - **Frontend** (`frontend/src/pages/admin/AdminDomains.tsx`): table of all domains (icon, name, key, builtin badge, active pill, edit button); edit drawer with General tab (display_name, icon, description, is_active toggle) + Config JSON tab (live JSON editor with validation); Sync button
  - **Navigation** (`frontend/src/components/layout/AdminLayout.tsx`): added "Domínios" nav link (Globe icon) between Usuários and Métricas
  - **Route** (`frontend/src/App.tsx`): added `/admin/domains` route under AdminLayout
  - **Backend** now has 73 HTTP routes, 16 DB tables
- [x] Phase 6: Fluxos completos para todos os 7 domínios restantes
  - `app/domains/_shared/flow_helpers.py` — helpers compartilhados por todos os domínios
  - **cleaning**: chatbot_flow.py (9 etapas) + products.py + pricing_rules.py (R$180-1100)
  - **electrician**: chatbot_flow.py (6 etapas) + products.py + pricing_rules.py (R$120-600)
  - **hvac**: chatbot_flow.py (7 etapas, BTU multipliers) + products.py + pricing_rules.py (R$150-800)
  - **pest_control**: chatbot_flow.py (8 etapas, pergunta pets) + products.py + pricing_rules.py (R$150-1920)
  - **plumbing**: chatbot_flow.py (7 etapas, local do problema) + products.py + pricing_rules.py (R$120-560)
  - **security_cameras**: chatbot_flow.py (7 etapas, cálculo por câmera) + products.py + pricing_rules.py (R$200-2500)
  - **glass_installation**: chatbot_flow.py (7 etapas, cálculo por m²) + products.py + pricing_rules.py (R$200-1500+)
  - Todos os domain.py atualizados: `has_pricing=True`, `get_pricing_service()` → pricing_rules
  - 100% dos fluxos simulados e validados; todos chegam a `quote_confirm` com `quote_preview` correto
- [x] Phase 5 (Parte 5 — produto): PDF, conversas, IA, janela 24h WhatsApp
  - **PDF melhorado** (`app/services/pdf_service.py`):
    - Parâmetro `logo_url`: baixa logo via requests + PIL, renderiza no cabeçalho com aspect ratio correto; degrada sem logo sem erro visual
    - Parâmetro `show_measures: bool`: quando False, oculta colunas Dimensões e Área da tabela, mostra rodapé informativo; quando True mantém tabela completa
    - `quotes.py` endpoint `GET /quotes/{id}/pdf` passa automaticamente `logo_url` e `show_measures_to_customer` das company settings
  - **Painel de conversas — preview de arquivos** (`frontend/src/pages/Conversations.tsx`):
    - Drawer lateral ao clicar em qualquer conversa
    - Renderização de mensagens com direção (in/out), avatar, horário, agrupamento por dia
    - Preview inline de: imagens (`<img>`), vídeos (`<video controls>`), áudio (`<audio controls>`), PDFs (iframe embed), documentos (ícone + download)
    - Botão de download para todos os tipos de mídia
    - Overlay com backdrop blur; fecha ao clicar fora
  - **Janela 24h WhatsApp** (`app/services/whatsapp_window_service.py`):
    - Detecta conversas em status BOT com `last_message_at` entre 22h-24h atrás
    - Envia nudge configurável por empresa via `extra_settings.whatsapp_nudge_message`
    - Evita duplicata na mesma janela via `bot_context.window_nudge_sent_at`
    - Endpoint `POST /api/v1/conversations/trigger-24h-check` (company_admin/master_admin) para chamar via cron
    - Configurável: `whatsapp_nudge_enabled`, `whatsapp_nudge_hours_before` (padrão 2h), `whatsapp_nudge_message`
  - **IA Assistente** (`app/services/ai_assistant_service.py`):
    - `humanize_bot_response(text, company_ctx, current_step)` — reformula mensagens do bot para mais naturais
    - `interpret_client_message(message, current_step, company_ctx)` — interpreta mensagens complexas do cliente
    - `explain_step_to_client(current_step)` — gera explicação amigável quando cliente estiver confuso
    - Usa `gpt-4o-mini`, degradação graciosa (retorna original se key ausente ou falha)
    - Integrada em `ConversationService._maybe_humanize_response()` — chamada APÓS o fluxo determinístico, ANTES do envio
    - Ativação opt-in por empresa: `extra_settings.ai_humanize_enabled = true`
    - Tom configurável: `extra_settings.ai_tone`
    - Regras de segurança: não altera valores, medidas, cálculos ou lógica do fluxo
    - `OPENAI_API_KEY` env var necessária para ativar; `openai==1.54.4` e `pillow==10.4.0` adicionados ao requirements.txt

## Notes

- `PNAddressCatalog`, `PNAddressPlant`, etc. had duplicate index definitions — `index=True` on FK columns was removed to fix startup.
- `DATABASE_URL` from Replit uses `postgresql://` scheme; config auto-converts to `postgresql+psycopg2://`.
- `CORS_ORIGINS` env var is stored as plain string; `cors_origins_list` computed field parses it.
- Frontend Vite proxies all `/api/*` requests to the backend on port 8000.
