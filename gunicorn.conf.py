"""
Gunicorn configuration for AlphaSync production deployment.

Usage:
  gunicorn -c gunicorn.conf.py app.main:app

Reference: https://docs.gunicorn.org/en/stable/settings.html
"""
import multiprocessing
import os

# ── Binding ────────────────────────────────────────────────────────────────
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# ── Workers ────────────────────────────────────────────────────────────────
# Uvicorn async workers (ASGI)
worker_class = "uvicorn.workers.UvicornWorker"

# Fórmula recomendada: 2-4 × CPUs
# VPS 2 vCPU → 2 workers (recomendado para 2 GB RAM)
# VPS 4 vCPU → 4 workers
# Ajuste via GUNICORN_WORKERS no .env se necessário.
cpu_count = multiprocessing.cpu_count()
_default_workers = min(max(2, cpu_count * 2), 8)  # máx 8 para evitar OOM
workers = int(os.getenv("GUNICORN_WORKERS", _default_workers))

# Threads por worker (útil para workloads mistos; manter 1 com UvicornWorker)
threads = int(os.getenv("GUNICORN_THREADS", 1))

# ── Timeouts ───────────────────────────────────────────────────────────────
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))

# ── Logging ────────────────────────────────────────────────────────────────
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Process naming ─────────────────────────────────────────────────────────
proc_name = "alphasync"

# ── Limits ─────────────────────────────────────────────────────────────────
# Reinicia cada worker após N requests para mitigar memory leaks
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 100))

# ── Worker recycling ───────────────────────────────────────────────────────
# preload_app=False necessário com UvicornWorker para evitar problemas de fork
preload_app = False
