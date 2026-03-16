# AlphaSync — Guia de Deploy em VPS

## Pré-requisitos na VPS
- Ubuntu 22.04+ ou Debian 12+
- Docker Engine 25+ e Docker Compose v2
- Mínimo 2 vCPU, 2 GB RAM, 20 GB disco
- Portas 80 e 443 abertas no firewall

---

## 1. Preparar o servidor

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

---

## 2. Clonar o projeto

```bash
git clone https://github.com/seu-usuario/alphasync.git /opt/alphasync
cd /opt/alphasync
```

---

## 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
nano .env  # ou vim .env
```

### Variáveis obrigatórias para produção:

```env
APP_ENV=production
APP_DEBUG=false
APP_VERSION=1.0.0

# Gere com: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<chave_aleatoria_forte_64_chars>

DATABASE_URL=postgresql+psycopg2://alphasync:<senha_forte>@postgres:5432/alphasync
REDIS_URL=redis://redis:6379/0

# Só o domínio do painel — sem wildcard em produção
CORS_ORIGINS=https://painel.seudominio.com.br

LOG_LEVEL=INFO

# WhatsApp (se usar chatbot)
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<token_do_webhook_meta>
WHATSAPP_APP_SECRET=<app_secret_meta>
```

### Variáveis do docker-compose:

```env
POSTGRES_USER=alphasync
POSTGRES_PASSWORD=<senha_banco>
POSTGRES_DB=alphasync
HTTP_PORT=80
HTTPS_PORT=443
```

---

## 4. Primeiro deploy

```bash
# Sobe os serviços (postgres + redis primeiro)
docker compose up -d postgres redis

# Aguarda o banco estar pronto (~10s) e roda migrations
docker compose --profile migrate up migrations

# Sobe o restante
docker compose up -d backend frontend nginx

# Verifica saúde
curl http://localhost/health
curl http://localhost/health/full
```

---

## 5. Seed do primeiro admin (só no primeiro deploy)

```bash
docker compose exec backend python scripts/seed_admin.py
```

---

## 6. Comandos de operação do dia a dia

```bash
# Ver logs em tempo real
docker compose logs -f backend
docker compose logs -f nginx

# Reiniciar só o backend
docker compose restart backend

# Ver status dos serviços
docker compose ps

# Parar tudo
docker compose down

# Parar e remover volumes (DESTRUIÇÃO de dados — irreversível)
docker compose down -v
```

---

## 7. Migrações em produção

```bash
# Gerar nova migration (rodar em DEV, commitar, e aplicar em prod)
alembic revision --autogenerate -m "descricao_da_mudanca"

# Aplicar no servidor (via docker)
docker compose --profile migrate up migrations

# Ou dentro do container
docker compose exec backend alembic upgrade head

# Ver histórico
docker compose exec backend alembic history

# Rollback da última migration
docker compose exec backend alembic downgrade -1
```

---

## 8. SSL / HTTPS com Let's Encrypt (Certbot)

```bash
# Instalar certbot
sudo apt install certbot

# Gerar certificado (com nginx parado)
sudo certbot certonly --standalone -d seudominio.com.br

# Copiar certificados
mkdir -p /opt/alphasync/nginx/certs
cp /etc/letsencrypt/live/seudominio.com.br/fullchain.pem nginx/certs/
cp /etc/letsencrypt/live/seudominio.com.br/privkey.pem nginx/certs/
```

Depois descomente as linhas de SSL no `nginx/nginx.conf` e reinicie o nginx.

---

## 9. Atualizações do sistema

```bash
cd /opt/alphasync

# Puxar código novo
git pull

# Rebuild e restart do backend
docker compose build backend
docker compose up -d backend

# Se houver migrations novas
docker compose --profile migrate up migrations

# Rebuild do frontend (se mudou código)
docker compose build frontend
docker compose up -d frontend nginx
```

---

## 10. Monitoramento e saúde

| Endpoint | Descrição |
|---|---|
| `GET /health` | Healthcheck básico (status do servidor) |
| `GET /health/full` | Healthcheck completo (DB + Redis) |

```bash
# Monitoramento simples com cron (a cada minuto)
* * * * * curl -sf http://localhost/health > /dev/null || docker compose restart backend
```

---

## 11. Backup do banco de dados

```bash
# Dump manual
docker compose exec postgres pg_dump -U alphasync alphasync > backup_$(date +%Y%m%d).sql

# Restaurar
docker compose exec -T postgres psql -U alphasync alphasync < backup_20240101.sql
```

---

## 12. Checklist final antes de ir ao ar

- [ ] `APP_ENV=production` no .env
- [ ] `APP_DEBUG=false` no .env
- [ ] `SECRET_KEY` com 64+ caracteres aleatórios (não é placeholder)
- [ ] `CORS_ORIGINS` contém apenas o(s) domínio(s) do painel — sem `*`
- [ ] `DATABASE_URL` e `REDIS_URL` apontam para os containers corretos
- [ ] `WHATSAPP_WEBHOOK_VERIFY_TOKEN` e `WHATSAPP_APP_SECRET` configurados
- [ ] Migrations rodaram sem erro: `alembic current` mostra `head`
- [ ] Seed do admin foi rodado: login em `/login` funciona
- [ ] `/health` retorna `{"status":"ok"}`
- [ ] `/health/full` retorna `{"status":"ok"}` com db e redis `ok`
- [ ] Docs desabilitados: `/docs` retorna 404 em produção
- [ ] Firewall: apenas portas 22, 80, 443 abertas
- [ ] SSL configurado e HTTPS funcionando (recomendado)
- [ ] Backup automático do PostgreSQL configurado (cron ou serviço)
- [ ] Logs rotacionados (`logrotate` ou Docker logging driver com limite)

---

## Comandos de diagnóstico rápido

```bash
# Status completo
docker compose ps

# Saúde do sistema
curl -s http://localhost/health/full | python3 -m json.tool

# Logs de erro do backend
docker compose logs backend --tail=50 | grep -i error

# Verificar migrations
docker compose exec backend alembic current

# Testar conexão com Redis
docker compose exec redis redis-cli ping

# Verificar banco
docker compose exec postgres psql -U alphasync -c "SELECT count(*) FROM users;"
```
