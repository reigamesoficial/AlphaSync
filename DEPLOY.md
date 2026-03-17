# AlphaSync — Guia de Deploy em VPS

## Pré-requisitos na VPS

- Ubuntu 22.04+ ou Debian 12+
- Docker Engine 25+ e Docker Compose v2
- Mínimo 2 vCPU, 2 GB RAM, 20 GB disco
- Portas 80 e 443 abertas no firewall
- Git instalado

---

## 1. Preparar o servidor

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
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
nano .env
```

### Variáveis obrigatórias para produção:

```env
APP_ENV=production
APP_DEBUG=false
APP_VERSION=1.0.0

# Gere com: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<chave_aleatoria_forte_64_chars>

# URLs dos containers (não altere os hostnames abaixo se usar Docker Compose)
DATABASE_URL=postgresql+psycopg2://alphasync:<senha_forte>@postgres:5432/alphasync
REDIS_URL=redis://redis:6379/0

# Apenas o domínio do painel — sem wildcard em produção
CORS_ORIGINS=https://painel.seudominio.com.br

LOG_LEVEL=INFO

# WhatsApp (se usar chatbot)
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<token_do_webhook_meta>
WHATSAPP_APP_SECRET=<app_secret_meta>
```

### Variáveis do Docker Compose (mesmo .env):

```env
POSTGRES_USER=alphasync
POSTGRES_PASSWORD=<senha_banco_forte>
POSTGRES_DB=alphasync
HTTP_PORT=80
HTTPS_PORT=443
```

### Trocar o server_name do nginx:

Edite `nginx/nginx.conf` e substitua:
```nginx
server_name localhost;
```
por:
```nginx
server_name painel.seudominio.com.br;
```

---

## 4. Primeiro deploy

```bash
cd /opt/alphasync

# 1. Sobe postgres e redis
docker compose up -d postgres redis

# 2. Aguarda estarem saudáveis (~15s) e roda migrations
docker compose --profile migrate up migrations
# Aguarda o container sair com código 0 antes de continuar

# 3. Seed do primeiro admin (somente no primeiro deploy)
docker compose --profile seed run --rm seed

# 4. Sobe o restante
docker compose up -d backend frontend nginx

# 5. Verifica saúde
curl http://localhost/health
curl http://localhost/health/full
```

---

## 5. Seed do primeiro admin

```bash
# Via profile (recomendado)
docker compose --profile seed run --rm seed

# Ou diretamente no container do backend
docker compose exec backend python scripts/seed_admin.py
```

> **IMPORTANTE:** Após o primeiro login, altere a senha do admin em `/perfil`.
> A senha padrão `changeme123` não deve permanecer em produção.

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

# Parar tudo (mantém dados nos volumes)
docker compose down

# Parar e remover volumes — DESTRÓI TODOS OS DADOS — irreversível
docker compose down -v
```

---

## 7. Migrações em produção

```bash
# Aplicar migrations pendentes
docker compose --profile migrate up migrations

# Ou dentro do container em execução
docker compose exec backend alembic upgrade head

# Ver histórico de migrations
docker compose exec backend alembic history

# Ver migration atual
docker compose exec backend alembic current

# Rollback da última migration (com cuidado)
docker compose exec backend alembic downgrade -1
```

> **Fluxo recomendado para updates:**
> 1. `git pull` no servidor
> 2. `docker compose --profile migrate up migrations`
> 3. `docker compose up -d --build backend`

---

## 8. Atualizações do sistema

```bash
cd /opt/alphasync

# Puxar código novo
git pull

# Rebuild e restart do backend
docker compose build backend
docker compose --profile migrate up migrations
docker compose up -d backend

# Rebuild do frontend (se mudou código)
docker compose build frontend
docker compose up -d frontend
```

---

## 9. SSL / HTTPS com Let's Encrypt (Certbot)

### Obter certificado

```bash
# Instalar certbot
sudo apt install certbot

# Parar nginx temporariamente
docker compose stop nginx

# Gerar certificado
sudo certbot certonly --standalone -d painel.seudominio.com.br

# Copiar para o projeto
mkdir -p /opt/alphasync/nginx/certs
sudo cp /etc/letsencrypt/live/painel.seudominio.com.br/fullchain.pem /opt/alphasync/nginx/certs/
sudo cp /etc/letsencrypt/live/painel.seudominio.com.br/privkey.pem /opt/alphasync/nginx/certs/
sudo chown $USER:$USER /opt/alphasync/nginx/certs/*
```

### Ativar SSL no nginx.conf

Descomente as seguintes seções em `nginx/nginx.conf`:

1. O bloco `server` de redirect HTTP→HTTPS
2. `listen 443 ssl;`
3. As linhas `ssl_certificate`, `ssl_certificate_key`, `ssl_protocols`, `ssl_ciphers`
4. O header `Strict-Transport-Security`
5. O volume de certs no `docker-compose.yml`

```bash
# Subir nginx novamente
docker compose up -d nginx
```

### Renovação automática do certificado

```bash
# Criar script de renovação
sudo tee /opt/alphasync/renew-ssl.sh << 'EOF'
#!/bin/bash
cd /opt/alphasync
docker compose stop nginx
certbot renew --quiet
cp /etc/letsencrypt/live/painel.seudominio.com.br/fullchain.pem nginx/certs/
cp /etc/letsencrypt/live/painel.seudominio.com.br/privkey.pem nginx/certs/
docker compose up -d nginx
EOF

sudo chmod +x /opt/alphasync/renew-ssl.sh

# Adicionar ao cron (renovação mensal às 3h da manhã)
sudo crontab -e
# Adicionar a linha:
# 0 3 1 * * /opt/alphasync/renew-ssl.sh >> /var/log/alphasync-ssl-renew.log 2>&1
```

---

## 10. Monitoramento e saúde

| Endpoint | Descrição |
|---|---|
| `GET /health` | Healthcheck básico (status do servidor) |
| `GET /health/full` | Healthcheck completo (DB + Redis) |

```bash
# Verificar saúde do sistema
curl -s http://localhost/health | python3 -m json.tool
curl -s http://localhost/health/full | python3 -m json.tool

# Monitoramento simples com cron (verifica a cada 5 minutos)
# Adicionar ao crontab:
# */5 * * * * curl -sf http://localhost/health > /dev/null || (cd /opt/alphasync && docker compose restart backend)
```

---

## 11. Rotação de logs

Os logs dos containers são gerenciados pelo Docker. Para evitar discos cheios:

```bash
# Configurar limite de logs do Docker (recomendado para VPS)
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
EOF

sudo systemctl restart docker
```

Ou configure por serviço adicionando a cada serviço no `docker-compose.yml`:
```yaml
logging:
  driver: json-file
  options:
    max-size: "50m"
    max-file: "5"
```

---

## 12. Backup do banco de dados

```bash
# Dump manual
docker compose exec postgres pg_dump -U alphasync alphasync > backup_$(date +%Y%m%d_%H%M).sql

# Restaurar
docker compose exec -T postgres psql -U alphasync alphasync < backup_20240101_0000.sql

# Backup automático diário (adicionar ao crontab)
# 0 2 * * * docker compose -f /opt/alphasync/docker-compose.yml exec -T postgres pg_dump -U alphasync alphasync > /opt/backups/alphasync_$(date +\%Y\%m\%d).sql
```

---

## 13. Checklist final antes de ir ao ar

### Ambiente
- [ ] `APP_ENV=production` no .env
- [ ] `APP_DEBUG=false` no .env
- [ ] `SECRET_KEY` com 64+ caracteres aleatórios gerados com `secrets.token_hex(32)` — não é placeholder
- [ ] `CORS_ORIGINS` contém apenas o(s) domínio(s) do painel — sem `*`
- [ ] `DATABASE_URL` e `REDIS_URL` apontam para os containers (`postgres:5432`, `redis:6379`)
- [ ] `POSTGRES_PASSWORD` é uma senha forte — não é `alphasync`

### Serviços
- [ ] `docker compose ps` mostra todos os serviços como `healthy` ou `running`
- [ ] Migrations rodaram sem erro: `docker compose exec backend alembic current` mostra `head`
- [ ] Seed do admin foi rodado e o login em `/login` funciona
- [ ] Senha padrão do admin foi alterada após o primeiro login

### Endpoints
- [ ] `curl /health` retorna `{"status":"ok"}`
- [ ] `curl /health/full` retorna `{"status":"ok"}` com `db` e `redis` como `"ok"`
- [ ] `/docs` retorna 404 em produção (documentação desabilitada)
- [ ] Frontend carrega corretamente no browser

### WhatsApp (se aplicável)
- [ ] `WHATSAPP_WEBHOOK_VERIFY_TOKEN` configurado e diferente do padrão
- [ ] `WHATSAPP_APP_SECRET` configurado com o app secret do Meta
- [ ] Webhook verificado no painel Meta

### Segurança
- [ ] Firewall: apenas portas 22, 80 (e 443 se SSL) abertas
- [ ] SSL configurado e HTTPS funcionando (recomendado para produção)
- [ ] Limites de logs do Docker configurados

### Opcional mas recomendado
- [ ] Backup automático do PostgreSQL configurado
- [ ] Renovação automática do SSL configurada
- [ ] Monitoramento de saúde via cron configurado

---

## 14. Diagnóstico rápido

```bash
# Status completo
docker compose ps

# Saúde do sistema
curl -s http://localhost/health/full | python3 -m json.tool

# Logs de erro do backend (últimas 50 linhas)
docker compose logs backend --tail=50 | grep -i "error\|critical\|exception"

# Verificar migrations
docker compose exec backend alembic current

# Testar conexão com Redis
docker compose exec redis redis-cli ping

# Verificar banco
docker compose exec postgres psql -U alphasync -c "SELECT count(*) FROM users;"

# Reiniciar serviço com problemas
docker compose restart backend

# Ver uso de recursos
docker stats --no-stream
```

---

## 15. Problemas comuns

| Problema | Causa provável | Solução |
|---|---|---|
| Backend não inicia | `SECRET_KEY` placeholder em produção | Gere uma chave forte no .env |
| `502 Bad Gateway` | Backend não está rodando ou não passou no healthcheck | `docker compose logs backend` para ver o erro |
| `503 Service Unavailable` | Frontend container não está saudável | `docker compose logs frontend` |
| Migrations falham | Banco não está acessível | Verificar `docker compose ps postgres` e logs |
| Login não funciona | Seed não foi rodado | `docker compose --profile seed run --rm seed` |
| CORS error no browser | `CORS_ORIGINS` incorreto | Verificar se o domínio do painel está no .env |
| OpenAI não humaniza | `OPENAI_API_KEY` não configurado | Configurar no .env — bot funciona sem ele |
| Webhook WhatsApp recusa | `WHATSAPP_APP_SECRET` incorreto | Verificar no painel Meta > App Settings |
