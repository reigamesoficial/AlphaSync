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

# Formula recomendada: 2-4 × CPUs
cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv("GUNICORN_WORKERS", max(2, cpu_count * 2 + 1)))

# Threads por worker (útil para workloads mistos)
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
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 100))

# ── Worker recycling ───────────────────────────────────────────────────────
# Reinicia workers periodicamente para evitar memory leaks
preload_app = False  # False com UvicornWorker para evitar problemas de fork
