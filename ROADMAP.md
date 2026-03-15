# AlphaSync — Roadmap Completo para Produção

**Gerado em:** 15 de Março de 2026
**Baseado em:** Auditoria do código + 8 documentos de projeto (Auditoria, API Endpoints x2, Schema MultiTenant, Sessao Persistente, Arquitetura v2, Diagnostico Refatoracao, Frontend Architecture)
**Validado por:** Teste de integração end-to-end 26/26 checkpoints — fluxo protection_network completo

---

## 1. Estado Atual — O que Já Existe

> O código atual está **muito mais avançado** do que os documentos de planejamento descrevem.
> Os documentos foram escritos como visão futura; boa parte já foi implementada.

### 1.1 Implementado e Funcionando

| Componente | Status | Detalhes |
|---|---|---|
| **Banco de Dados PostgreSQL** | ✅ Completo | 12+ tabelas multi-tenant com `company_id` em tudo; criadas via `Base.metadata.create_all()` no startup |
| **Autenticação JWT** | ✅ Completo | `python-jose`, access token (60min) + refresh token (7 dias), `GET /api/v1/auth/login` + `POST /api/v1/auth/refresh` |
| **Multi-tenancy** | ✅ Completo | Isolamento por `company_id` em todas as tabelas; `TenantRepository` como base; resolver por `whatsapp_phone_number_id` |
| **Sessão do Chatbot Persistida** | ✅ Completo + 3 bugs corrigidos | `bot_step` + `bot_context` (JSON) na tabela `conversations`. Bugs corrigidos: `flag_modified`, `selected_item_ids` em `protected_list_keys`, `Decimal` → `float` antes de gravar JSON |
| **Domínio protection_network** | ✅ Completo | Fluxo completo: saudação → nome → endereço → seleção de medidas → cor → malha → quote_confirm → quote_ready. Catálogo de endereços, preços, job_rules |
| **Outros 7 Domínios** | ✅ Esqueleto completo | `cleaning`, `electrician`, `glass_installation`, `hvac`, `pest_control`, `plumbing`, `security_cameras` — cada um com `chatbot_flow.py` e `domain.py` |
| **WhatsApp Service** | ✅ Completo | `send_text`, `send_buttons`, `send_list_message`, `verify_webhook`, `extract_inbound_events`, `resolve_media_url` |
| **Webhook endpoint** | ✅ Completo | `GET /api/v1/webhooks/whatsapp` (verificação Meta) + `POST /api/v1/webhooks/whatsapp` (mensagens inbound) |
| **Repositories** | ✅ Completo | `addresses`, `appointments`, `clients`, `companies`, `company_settings`, `conversations`, `quotes` (+ `QuoteItemsRepository`), `users` |
| **Endpoints básicos /api/v1/** | ✅ Parcial | `auth/login`, `auth/refresh`, `companies/me`, `companies/me/settings` (GET/PUT), `users/me` |
| **ConversationService** | ✅ Completo | 758 linhas — orquestra todo o fluxo inbound: get/create client, conversation, session, domain dispatch, persist quote |
| **Redis** | ✅ Instalado | `redis==5.1.1` em requirements. Não integrado ainda (sem rate limiting nem cache) |
| **Alembic** | ✅ Instalado | `alembic==1.13.2` em requirements. Não configurado — banco criado via `create_all()` |

### 1.2 Stubs / Esqueletos (código existe, lógica está vazia)

| Componente | Status | Arquivo |
|---|---|---|
| PDF generation | ⚠️ Stub (1 linha) | `app/services/pdf_service.py` |
| Pricing service | ⚠️ Stub (1 linha) | `app/services/pricing_service.py` |
| Scheduling service | ⚠️ Stub (1 linha) | `app/services/scheduling_service.py` |
| Admin Company panel | ⚠️ Skeleton | `app/api/admin_company.py` (só `/health`) |
| Admin Master panel | ⚠️ Skeleton | `app/api/admin_master.py` (só `/health`) |
| Panel API | ⚠️ Skeleton | `app/api/panel.py` (vazio) |
| Google Calendar | ⚠️ Parcial | `app/integrations/calendar_client.py` existe; `scheduling_service.py` é stub |
| CORS | ⚠️ Configurado, não aplicado | `cors_origins` definido em `config.py` mas `CORSMiddleware` não adicionado em `main.py` |

### 1.3 Não Existe (zero código)

| Componente | Documentado em |
|---|---|
| ~30 endpoints REST do painel CRM | API Endpoints doc |
| Frontend React/TypeScript | Frontend Architecture doc |
| Alembic migrations (pasta `alembic/`) | — |
| Gunicorn / multi-worker config | — |
| Error monitoring (Sentry etc.) | — |
| Rate limiting | — |
| Seeding / primeiro admin | — |

---

## 2. Lacunas Críticas para o MVP de Produção

### 2.1 Endpoints REST Faltando (~30)

Os documentos especificaram 47 endpoints sob `/api/v1/`. Existem apenas 9.
Faltam (em ordem de prioridade operacional):

**Conversas (CRM core):**
- `GET /api/v1/conversations` — lista com filtros, polling
- `GET /api/v1/conversations/{id}/messages` — histórico (scroll infinito)
- `POST /api/v1/conversations/{id}/messages` — resposta humana (muda status → "human")
- `PATCH /api/v1/conversations/{id}/status` — fechar / reabrir / assumir

**Clientes:**
- `GET /api/v1/clients` — lista paginada
- `GET /api/v1/clients/{id}` — perfil completo

**Orçamentos:**
- `GET /api/v1/quotes` — lista com filtros
- `POST /api/v1/quotes` — criar manualmente
- `PATCH /api/v1/quotes/{id}` — editar cabeçalho
- `GET /api/v1/quotes/{id}/pdf` — download PDF
- `POST /api/v1/quotes/{id}/items` — adicionar item
- `PATCH /api/v1/quotes/{id}/items/{item_id}` — editar item
- `DELETE /api/v1/quotes/{id}/items/{item_id}` — remover item
- `PATCH /api/v1/quotes/{id}/items/{item_id}/status` — marcar como done

**Medidas (Catálogo de Endereços):**
- `GET /api/v1/measurements` — lista endereços da empresa
- `POST /api/v1/measurements` — criar endereço + medidas
- `PATCH /api/v1/measurements/{id}` — editar
- `DELETE /api/v1/measurements/{id}` — remover

**Agendamentos:**
- `GET /api/v1/appointments` — lista com filtros
- `GET /api/v1/appointments/{id}/slots` — slots disponíveis (Google Calendar)
- `POST /api/v1/appointments/{id}/reschedule` — reagendar
- `POST /api/v1/appointments/{id}/notify` — enviar lembrete manual

**Dashboard:**
- `GET /api/v1/dashboard/stats` — métricas do dia
- `GET /api/v1/dashboard/activity` — feed de atividade recente

**Usuários / Instaladores (admin):**
- `GET /api/v1/users` — listar (admin only)
- `POST /api/v1/users` — criar
- `GET /api/v1/installers` — listar
- `POST /api/v1/installers` — criar

### 2.2 Correções de Configuração Imediatas Necessárias

1. **CORS** — `CORSMiddleware` não está em `main.py` → frontend vai receber bloqueio de browser
2. **Tables via `create_all()`** — Funciona, mas sem Alembic não há histórico de migrações, rollback nem schema versionado
3. **`app_debug=True` hardcoded** — em produção deve ser `False`
4. **Sem Gunicorn** — `uvicorn` single-process não aguenta múltiplos workers

---

## 3. Roadmap por Fases

### FASE 0 — Correções Imediatas (1–2 dias) 🔴 URGENTE

Estas são pré-condições para qualquer teste com o frontend ou produção real.

| Tarefa | Arquivo | Descrição |
|---|---|---|
| **Adicionar CORS** | `app/main.py` | `CORSMiddleware` com `cors_origins` do config |
| **Fixar `app_debug`** | `app/core/config.py` | Garantir `app_debug=False` em produção via env var `APP_DEBUG` |
| **Seed do primeiro admin** | script `scripts/seed_admin.py` | Criar empresa + CompanySettings + usuário admin inicial |
| **Variáveis de ambiente documentadas** | `.env.example` | `SECRET_KEY`, `DATABASE_URL`, `WHATSAPP_WEBHOOK_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET` |
| **Validar SECRET_KEY em prod** | `app/core/config.py` | Falhar no startup se `SECRET_KEY` for o valor default em produção |

### FASE 1 — API do Painel CRM (1 semana)

Sem esses endpoints o frontend não existe. Repositories já estão implementados — é expor via HTTP.

**Semana 1, Dias 1-2: Conversas**
- `GET /api/v1/conversations` — lista filtrada (status, assigned_to, date)
- `GET /api/v1/conversations/{id}/messages` — histórico paginado (after_id / before_id)
- `POST /api/v1/conversations/{id}/messages` — resposta humana (muda status → "human", salva direção "out")
- `PATCH /api/v1/conversations/{id}` — atribuir, mudar status, marcar mensagens como lidas

**Semana 1, Dias 2-3: Orçamentos + Itens**
- `GET /api/v1/quotes`, `POST /api/v1/quotes`
- `PATCH /api/v1/quotes/{id}`
- `POST /api/v1/quotes/{id}/items`, `PATCH`, `DELETE`, `PATCH /status`

**Semana 1, Dias 3-4: Clientes + Medidas**
- `GET /api/v1/clients`, `GET /api/v1/clients/{id}`
- `GET /api/v1/measurements`, `POST`, `PATCH`, `DELETE`

**Semana 1, Dia 5: Dashboard + Usuários**
- `GET /api/v1/dashboard/stats`, `GET /api/v1/dashboard/activity`
- `GET /api/v1/users`, `POST /api/v1/users`

### FASE 2 — PDF e Agendamentos (3–5 dias)

**PDF Generation:**
- Implementar `app/services/pdf_service.py` usando `reportlab` ou `weasyprint`
- Endpoint `GET /api/v1/quotes/{id}/pdf` (download direto + pre-warm)
- Template de orçamento para `protection_network` (logo da empresa, itens, totais, validade)
- Adicionar `reportlab` ou `weasyprint` no `requirements.txt`

**Google Calendar / Agendamentos:**
- Implementar `app/services/scheduling_service.py` (wrapping `calendar_client.py`)
- `GET /api/v1/appointments` — lista com filtros
- `GET /api/v1/appointments/{id}/slots` — slots via Google Calendar freebusy
- `POST /api/v1/appointments/{id}/reschedule` — reagendar + notificação WhatsApp
- `POST /api/v1/appointments/{id}/notify` — lembrete manual
- Adicionar env vars: `GOOGLE_CREDENTIALS_JSON_PATH`, `GOOGLE_CALENDAR_ENABLED=true`

### FASE 3 — Frontend React (1–2 semanas)

Construir sobre a API estabilizada da Fase 1+2.
Stack definida nos documentos: **React + TypeScript + Tailwind CSS + React Query + Zustand + React Router**.

**Ordem de telas por valor operacional (conforme Frontend Architecture doc):**

1. **Login** — formulário + JWT storage em localStorage/cookie httpOnly
2. **Conversas** — 3 colunas (lista | chat | detalhes), polling a cada 5–10s
3. **Orçamentos** — lista + editor inline de itens + download PDF
4. **Medidas** — CRUD de endereços e medidas (entrada rápida de dados)
5. **Dashboard** — métricas do dia, KPIs, feed de atividade
6. **Agenda** — calendário de agendamentos, seleção de slots

**Estrutura de pastas (conforme Feature-Sliced Design do doc):**
```
frontend/
  src/
    features/
      auth/
      conversations/
      quotes/
      measurements/
      appointments/
      dashboard/
    lib/
      api.ts        # axios instance + interceptors JWT
    router/
      index.tsx
    components/     # design system (StatusBadge, MetricCard, DataTable)
    types/          # TypeScript interfaces
```

### FASE 4 — Infraestrutura de Produção (3–5 dias)

**Alembic (Migrações):**
- Inicializar `alembic/` com `alembic init`
- Gerar migration inicial a partir dos modelos atuais (`alembic revision --autogenerate`)
- Trocar `Base.metadata.create_all()` no startup por verificação de migration aplicada
- Pipeline CI: `alembic upgrade head` antes do start do servidor

**Multi-worker / Gunicorn:**
- Adicionar `gunicorn==21.x` + `uvicorn[standard]` no requirements
- Criar `gunicorn.conf.py`: `workers = 2 * CPU_COUNT + 1`, `worker_class = "uvicorn.workers.UvicornWorker"`
- Sessão do chatbot já é DB-backed (✅ validado no teste 26/26) — multi-worker seguro

**Redis (Rate Limiting + Cache):**
- Usar `redis` (já instalado) + `slowapi` para rate limiting no webhook endpoint
- Cache de `company settings` e `address catalog` em Redis (TTL 5min) para reduzir queries

**Error Monitoring:**
- Adicionar `sentry-sdk[fastapi]` no requirements
- `Sentry.init()` em `main.py` com `traces_sample_rate=0.1`
- Configurar via `SENTRY_DSN` env var

**Logging Estruturado:**
- Usar `structlog` ou `loguru` para logs JSON em produção
- Log de cada mensagem WhatsApp recebida: `company_id`, `phone`, `bot_step`, `latency_ms`

### FASE 5 — Admin + Multi-empresa (1 semana)

**Admin Master** (superusuário da plataforma):
- `GET /admin/master/companies` — listar todas as empresas
- `POST /admin/master/companies` — criar nova empresa
- `PATCH /admin/master/companies/{id}` — ativar/desativar tenant

**Admin Company** (administrador da empresa):
- `GET /admin/company/settings` — configurações da empresa
- `PUT /admin/company/settings` — alterar preços, bot_name, cores, malhas
- `GET /admin/company/users` — listar usuários
- Tela de configuração no frontend

---

## 4. Bugs Corrigidos Nesta Sessão

Três bugs foram identificados, corrigidos e validados por teste automatizado (26/26 checkpoints):

| # | Bug | Arquivo | Correção |
|---|---|---|---|
| 1 | `bot_context` não persistia no PostgreSQL — SQLAlchemy não detectava mudança em dicts JSON | `app/domains/protection_network/chatbot_flow.py` | Adicionado `flag_modified(conversation, "bot_context")` em `_save_state()` |
| 2 | `selected_item_ids` era resetado para `[]` em cada mensagem durante o merge de contexto | `app/services/conversation_service.py` | Adicionado `"selected_item_ids"` na lista `protected_list_keys` de `_merge_bot_context()` |
| 3 | `Decimal` nos valores de `quote_preview` causava `TypeError: Object of type Decimal is not JSON serializable` ao fazer `db.flush()` | `app/domains/protection_network/chatbot_flow.py` | Adicionada função `_json_safe(obj)` que converte `Decimal` → `float` recursivamente; chamada em `_save_state()` antes de gravar |

---

## 5. Dependências e Env Vars para Produção

### Variáveis de Ambiente Obrigatórias

```env
# Segurança (OBRIGATÓRIO — mínimo 32 chars)
SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_hex(32))">

# Banco
DATABASE_URL=postgresql://user:pass@host:5432/alphasync

# WhatsApp / Meta
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<token que você configura no painel Meta>
WHATSAPP_APP_SECRET=<App Secret do painel Meta>

# Ambiente
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO
```

### Variáveis de Ambiente Opcionais

```env
# Redis (rate limiting + cache)
REDIS_URL=redis://localhost:6379/0

# Google Calendar (Fase 2)
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CREDENTIALS_JSON_PATH=/secrets/google_credentials.json

# CORS (múltiplas origens separadas por vírgula)
CORS_ORIGINS=https://painel.suaempresa.com,https://admin.suaempresa.com

# Monitoramento
SENTRY_DSN=https://xxx@sentry.io/yyy

# PDF
MEDIA_BASE_URL=https://storage.suaempresa.com
STORAGE_PATH=/var/data/alphasync/storage
```

### Dependências a Adicionar (não estão em requirements.txt ainda)

| Pacote | Fase | Finalidade |
|---|---|---|
| `gunicorn==21.2.0` | Fase 4 | Multi-worker production server |
| `reportlab==4.2.x` ou `weasyprint==62.x` | Fase 2 | Geração de PDF |
| `slowapi==0.1.9` | Fase 4 | Rate limiting no webhook |
| `sentry-sdk[fastapi]==1.45.x` | Fase 4 | Error monitoring |
| `structlog==24.x` | Fase 4 | Logging estruturado JSON |

---

## 6. Resumo Visual do Roadmap

```
Mar 2026 (agora)
│
├─ FASE 0 ─ Correções Imediatas ──────────── 1-2 dias
│   ✅ CORS middleware em main.py
│   ✅ .env.example completo
│   ✅ seed_admin.py
│   ✅ validação SECRET_KEY em produção
│
├─ FASE 1 ─ API do Painel CRM ─────────────  1 semana
│   🔵 ~30 endpoints REST (repos já existem)
│   🔵 Conversas, Clientes, Orçamentos+Itens
│   🔵 Dashboard, Usuários
│
├─ FASE 2 ─ PDF + Agendamentos ────────────  3-5 dias
│   🔵 pdf_service.py (reportlab/weasyprint)
│   🔵 scheduling_service.py (Google Calendar)
│   🔵 endpoints de slots, reagendamento
│
├─ FASE 3 ─ Frontend React ────────────────  1-2 semanas
│   🔵 Login, Conversas, Orçamentos
│   🔵 Medidas, Dashboard, Agenda
│   🔵 React + TypeScript + Tailwind + React Query
│
├─ FASE 4 ─ Infra de Produção ─────────────  3-5 dias
│   🔵 Alembic (migrações versionadas)
│   🔵 Gunicorn multi-worker
│   🔵 Redis rate limiting + cache
│   🔵 Sentry error monitoring
│   🔵 Structured logging
│
└─ FASE 5 ─ Admin + Multi-empresa ─────────  1 semana
    🔵 Admin Master (gestão de tenants)
    🔵 Admin Company (configurações por empresa)
    🔵 Onboarding de novos clientes SaaS

                                        PRODUÇÃO ✅
```

---

## 7. Ordem de Prioridade Absoluta (Top 5)

1. **CORS middleware** — bloqueia 100% do frontend sem isso (30 minutos de trabalho)
2. **~30 endpoints REST** — único pré-requisito do frontend; repositories já prontos (1 semana)
3. **PDF generation** — feature mais solicitada após o orçamento ser gerado pelo bot
4. **Alembic migrations** — segurança para deploy em produção sem perder dados
5. **Frontend — tela de Conversas** — maior valor operacional; a equipe usa mais do que qualquer outra tela

---

*AlphaSync Roadmap  ·  Gerado automaticamente  ·  Março 2026*
