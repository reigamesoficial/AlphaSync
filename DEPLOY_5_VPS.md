# AlphaSync — Guia de Deploy em 5 VPS

## Arquitetura

```
Internet
   │
   ▼
┌──────────────────────────────┐
│  VPS 1 — EDGE               │  80/443 (público)
│  nginx + SSL + Frontend      │
└──────────────┬───────────────┘
               │ proxy /api/*
               ▼
┌──────────────────────────────┐
│  VPS 2 — APP                │  8000 (privado)
│  FastAPI + Gunicorn          │
└─────┬──────────────┬─────────┘
      │              │
      ▼              ▼
┌──────────┐  ┌──────────────────────────┐
│  VPS 3   │  │  VPS 4 — WORKER         │
│  DB      │  │  Redis + Scheduler       │
│  PG 16   │◄─┤  (lembretes, jobs)       │
└──────────┘  └──────────────────────────┘

┌──────────────────────────────┐
│  VPS 5 — STAGING            │  8080 (privado/restrito)
│  Stack completa de homolog.  │
└──────────────────────────────┘
```

---

## Ordem de Subida

1. **VPS 3** — Banco de dados (PostgreSQL)
2. **VPS 4** — Worker/Redis
3. **VPS 2** — App (backend FastAPI) + migrations
4. **VPS 1** — Edge (nginx + frontend)
5. **VPS 5** — Staging (independente, sobe à parte)

---

## Pré-requisitos Comuns

- Docker Engine 24+ e Docker Compose v2 em cada VPS
- Acesso SSH à root ou usuário com sudo
- Rede privada entre as VPS (firewall configurado)
- Repositório clonado em cada VPS que precisar do código

```bash
# Em cada VPS que precisar do código (VPS 2, 4, 5):
git clone https://seu-repositorio.git /opt/alphasync
cd /opt/alphasync
```

---

## VPS 3 — DATABASE (PostgreSQL)

### Setup

```bash
cd /opt/alphasync/deploy/db
cp .env.example .env
nano .env  # Preencher POSTGRES_PASSWORD
mkdir -p backups
docker compose up -d
docker compose ps  # postgres deve estar healthy
```

### Verificação

```bash
docker exec alphasync_db pg_isready -U alphasync -d alphasync
# saída: /var/run/postgresql:5432 - accepting connections
```

### Firewall

```bash
# Liberar porta 5432 apenas para IPs privados das VPS 2 e VPS 4
ufw allow from VPS2_PRIVATE_IP to any port 5432
ufw allow from VPS4_PRIVATE_IP to any port 5432
ufw deny 5432
```

### Backup automático

```bash
# Configurar cron para backup diário às 2h
crontab -e
# Adicionar:
0 2 * * * /opt/alphasync/deploy/db/backup.sh >> /var/log/alphasync_backup.log 2>&1
```

### Restore

```bash
# Listar backups disponíveis
ls deploy/db/backups/

# Restaurar backup específico
gunzip -c deploy/db/backups/alphasync_20250101_020000.sql.gz \
  | docker exec -i alphasync_db psql -U alphasync -d alphasync
```

---

## VPS 4 — WORKER (Redis + Scheduler)

### Setup

```bash
cd /opt/alphasync/deploy/worker
cp .env.example .env
nano .env  # Preencher DATABASE_URL (apontar para VPS 3), SECRET_KEY, REDIS_PASSWORD

# Build da imagem do worker (mesma do app)
docker compose build

docker compose up -d
docker compose logs -f worker  # Verificar startup do scheduler
```

### Verificação

```bash
# Redis funcionando
docker exec alphasync_redis redis-cli -a REDIS_PASSWORD ping
# saída: PONG

# Worker rodando e conectado ao banco
docker logs alphasync_worker | grep "Scheduler iniciado"
```

### Firewall

```bash
# Redis só acessível para VPS 2 (caso Redis seja usado pelo app no futuro)
ufw allow from VPS2_PRIVATE_IP to any port 6379
ufw deny 6379
```

---

## VPS 2 — APP (FastAPI + Gunicorn)

### Setup

```bash
cd /opt/alphasync/deploy/app
cp .env.example .env
nano .env  # DATABASE_URL (VPS 3), REDIS_URL (VPS 4), SECRET_KEY, CORS_ORIGINS, WhatsApp, OpenAI

# Build
docker compose build

# Migrations — RODAR ANTES de subir o app
docker compose run --rm backend alembic upgrade head

# Seed do primeiro admin (apenas na primeira vez)
docker compose run --rm backend python scripts/seed_admin.py

# Subir
docker compose up -d
docker compose ps  # backend deve estar healthy
```

### Verificação

```bash
curl http://localhost:8000/health
# saída: {"status":"ok","services":{"database":{"status":"ok"},"redis":{"status":"ok"}}}
```

### Confirmar scheduler desabilitado

```bash
docker logs alphasync_app | grep "Scheduler"
# saída esperada: Scheduler : desabilitado (ENABLE_SCHEDULER=false)
```

### Firewall

```bash
# Porta 8000 só acessível para VPS 1 (EDGE)
ufw allow from VPS1_PRIVATE_IP to any port 8000
ufw deny 8000
```

---

## VPS 1 — EDGE (Nginx + SSL + Frontend)

### Build do frontend

```bash
# Rodar no ambiente de desenvolvimento ou CI/CD
cd /caminho/para/alphasync/frontend
npm ci
npm run build
# Copiar o dist/ para a VPS 1
scp -r dist/ user@VPS1:/opt/alphasync/deploy/edge/html/
```

### SSL com Let's Encrypt

```bash
# Instalar certbot localmente e obter certificados antes de subir o nginx
apt install certbot
certbot certonly --standalone -d app.suaempresa.com

# Copiar certificados
cp /etc/letsencrypt/live/app.suaempresa.com/fullchain.pem deploy/edge/certs/
cp /etc/letsencrypt/live/app.suaempresa.com/privkey.pem   deploy/edge/certs/
chmod 600 deploy/edge/certs/*.pem
```

### Configurar nginx

```bash
cd /opt/alphasync/deploy/edge

# Editar nginx.conf:
# 1. Substituir APP_VPS2_HOST pelo IP privado da VPS 2
# 2. Substituir YOUR_DOMAIN pelo domínio real
sed -i 's/APP_VPS2_HOST/10.0.0.2/g' nginx.conf
sed -i 's/YOUR_DOMAIN/app.suaempresa.com/g' nginx.conf

cp .env.example .env
nano .env
```

### Subir

```bash
docker compose up -d
docker compose ps
curl -I https://app.suaempresa.com/health
```

---

## VPS 5 — STAGING

### Setup completo

```bash
cd /opt/alphasync/deploy/staging
cp .env.example .env
nano .env  # Preencher valores de staging (chaves DIFERENTES de produção)

# Build de tudo
docker compose build

# Migrations
docker compose run --rm backend alembic upgrade head

# Seed admin de staging
docker compose run --rm backend python scripts/seed_admin.py

# Subir
docker compose up -d
docker compose ps
```

### Acesso

```bash
# Painel disponível em:
http://VPS5_IP:8080

# Health check
curl http://VPS5_IP:8080/health
```

### Reset total de staging

```bash
# Apaga todos os dados e reinicia do zero
docker compose down -v
docker compose up -d
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/seed_admin.py
```

---

## Migrations em Produção

```bash
# Sempre rodar na VPS 2 antes de subir nova versão
cd /opt/alphasync/deploy/app

# Ver status das migrations
docker compose run --rm backend alembic current

# Aplicar migrations pendentes
docker compose run --rm backend alembic upgrade head

# Histórico
docker compose run --rm backend alembic history --verbose
```

---

## Atualização de Versão (Deploy)

```bash
# Em cada VPS com código (2, 4, 5):
cd /opt/alphasync
git pull origin main

# VPS 2 — App
cd deploy/app
docker compose build
docker compose run --rm backend alembic upgrade head
docker compose up -d --force-recreate

# VPS 4 — Worker
cd deploy/worker
docker compose build
docker compose up -d --force-recreate

# VPS 1 — Frontend (rebuild + deploy)
# (build no CI/CD e copiar dist/ para edge/html/)
docker compose restart nginx
```

---

## Health Checks

### VPS 2 — Backend completo

```bash
curl http://VPS2_PRIVATE_IP:8000/health
# Resposta esperada:
# {"status":"ok","services":{"database":{"status":"ok"},"redis":{"status":"ok"}}}
```

### VPS 1 — Edge/Frontend

```bash
curl https://app.suaempresa.com/health
# Resposta esperada: ok

curl https://app.suaempresa.com/api/v1/health
# Ou via API: {"status":"ok",...}
```

### VPS 3 — Banco

```bash
docker exec alphasync_db pg_isready -U alphasync
```

### VPS 4 — Redis + Worker

```bash
docker exec alphasync_redis redis-cli ping
docker logs alphasync_worker --tail=50
```

---

## Comunicação entre VPS — Teste

```bash
# Da VPS 2, testar conectividade com VPS 3 (banco)
docker compose run --rm backend python -c "
from app.db.connection import engine
with engine.connect() as c:
    print('DB OK:', c.execute(__import__('sqlalchemy').text('SELECT 1')).scalar())
"

# Da VPS 2, testar conectividade com VPS 4 (Redis)
docker compose run --rm backend python -c "
from app.core.redis_client import get_redis
r = get_redis()
r.ping()
print('Redis OK')
"
```

---

## Configuração de Domínio

1. Apontar DNS `app.suaempresa.com` para o **IP público da VPS 1**
2. Esperar propagação (até 48h, geralmente minutos)
3. Verificar: `dig app.suaempresa.com +short`
4. Obter certificado SSL: `certbot certonly --standalone -d app.suaempresa.com`
5. Atualizar `nginx.conf` com domínio e caminhos dos certificados
6. Reiniciar nginx: `docker compose restart nginx`

### Webhook WhatsApp

O webhook da Meta deve apontar para:
```
https://app.suaempresa.com/api/v1/webhook/whatsapp
```

---

## Variáveis Críticas por VPS

| Variável | VPS 2 (APP) | VPS 4 (WORKER) | VPS 5 (STAGING) |
|---|---|---|---|
| `SECRET_KEY` | Mesma em todas | Mesma que APP | Diferente de prod |
| `DATABASE_URL` | → VPS 3 | → VPS 3 | → postgres local |
| `REDIS_URL` | → VPS 4 | localhost | → redis local |
| `ENABLE_SCHEDULER` | `false` | `true` | `false` (worker separado) |
| `APP_ENV` | `production` | `production` | `staging` |
| `APP_DEBUG` | `false` | `false` | `false` |
| `CORS_ORIGINS` | Domínio VPS 1 | — | IP VPS 5 |

---

## Portas por VPS

| VPS | Porta | Exposição | Protocolo |
|-----|-------|-----------|-----------|
| VPS 1 (EDGE) | 80 | Pública | HTTP → redirect HTTPS |
| VPS 1 (EDGE) | 443 | Pública | HTTPS |
| VPS 2 (APP) | 8000 | Privada (só VPS 1) | HTTP |
| VPS 3 (DB) | 5432 | Privada (só VPS 2 e 4) | TCP |
| VPS 4 (WORKER) | 6379 | Privada (só VPS 2) | TCP |
| VPS 5 (STAGING) | 8080 | Restrita (acesso controlado) | HTTP |

---

## Troubleshooting

### Backend não conecta no banco

```bash
# Verificar se a porta 5432 está acessível
docker compose run --rm backend nc -zv VPS3_PRIVATE_IP 5432

# Verificar logs do postgres
docker logs alphasync_db --tail=50

# Verificar firewall da VPS 3
ufw status
```

### Frontend não carrega / 502 Bad Gateway

```bash
# Verificar se o backend está respondendo na VPS 2
curl http://VPS2_PRIVATE_IP:8000/health

# Verificar configuração do nginx
docker exec alphasync_edge nginx -t

# Logs do nginx
docker logs alphasync_edge --tail=100
```

### Worker não envia lembretes

```bash
# Verificar logs do worker
docker logs alphasync_worker --tail=100

# Verificar conexão do worker com o banco
docker compose -f deploy/worker/docker-compose.yml run --rm worker python -c "
from app.db.connection import engine
with engine.connect() as c:
    print('DB OK')
"
```

### Migrations falharam

```bash
# Ver estado atual
docker compose run --rm backend alembic current

# Ver histórico
docker compose run --rm backend alembic history

# Reverter migration (se necessário)
docker compose run --rm backend alembic downgrade -1
```

### Certificado SSL expirado

```bash
# Na VPS 1
docker compose run --rm certbot renew
docker compose restart nginx
```

---

## Checklist Final de Validação

- [ ] VPS 3: `pg_isready` retorna OK
- [ ] VPS 4: `redis-cli ping` retorna PONG
- [ ] VPS 4: Worker logs mostram "Scheduler iniciado"
- [ ] VPS 2: `/health` retorna `{"status":"ok"}`
- [ ] VPS 2: Logs não mostram scheduler iniciado (`ENABLE_SCHEDULER=false`)
- [ ] VPS 2: Migrations aplicadas (`alembic current` = HEAD)
- [ ] VPS 1: `https://app.suaempresa.com` carrega o painel
- [ ] VPS 1: `https://app.suaempresa.com/api/v1/health` retorna OK
- [ ] Login funciona: `admin@alphasync.app`
- [ ] Webhook WhatsApp configurado na Meta e respondendo ao verify
- [ ] Backup automático configurado na VPS 3
