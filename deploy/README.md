# AlphaSync — Estrutura de Deploy Distribuído

## Arquitetura

```
VPS 1 (EDGE)     VPS 2 (APP)      VPS 3 (DATABASE)   VPS 4 (WORKER)   VPS 5 (STAGING)
─────────────    ─────────────    ────────────────    ───────────────  ───────────────
nginx            FastAPI          PostgreSQL 16       Redis 7          Stack completa
SSL/TLS          Gunicorn         Volume persistente  Scheduler        de homologação
Frontend SPA     API REST         Backups             Lembretes
Proxy reverso    Webhook WA
                 PDFs
```

## Pasta por VPS

| Pasta | VPS | Serviços |
|-------|-----|----------|
| `edge/` | VPS 1 | nginx, SSL, frontend estático |
| `app/` | VPS 2 | backend FastAPI + Gunicorn |
| `db/` | VPS 3 | PostgreSQL + backups |
| `worker/` | VPS 4 | Redis + Worker (scheduler) |
| `staging/` | VPS 5 | Stack completa de homologação |

## Guia completo

Leia `DEPLOY_5_VPS.md` na raiz do projeto para o passo-a-passo completo.
