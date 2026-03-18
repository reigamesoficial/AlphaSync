"""
AlphaSync — Worker standalone para VPS 4 (WORKER).

Executa o scheduler de tarefas periódicas (lembretes, etc.) como processo
independente, sem carregar o servidor FastAPI/Gunicorn.

Uso:
  python -m app.worker

Em Docker (VPS 4):
  docker compose up -d worker

Variáveis de ambiente necessárias:
  DATABASE_URL  — conexão com PostgreSQL (VPS 3)
  REDIS_URL     — conexão com Redis (local na VPS 4)
  SECRET_KEY    — mesma chave do app
  APP_ENV       — production
  LOG_LEVEL     — INFO
"""
from __future__ import annotations

import logging
import signal
import sys
import time

from app.core.config import settings


def _configure_logging() -> None:
    import json

    class _JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
            }
            if record.exc_info:
                payload["exc"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False)

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level, logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
    root.handlers = [handler]


def main() -> None:
    _configure_logging()
    logger = logging.getLogger("alphasync.worker")

    logger.info("=" * 60)
    logger.info("  AlphaSync Worker — startup")
    logger.info("=" * 60)
    logger.info(f"  Ambiente : {settings.app_env.upper()}")
    logger.info(f"  Database : {settings.masked_database_url}")
    logger.info(f"  Redis    : {settings.redis_url}")
    logger.info("=" * 60)

    from app.core import scheduler as _scheduler

    _scheduler.start()
    logger.info("  Scheduler iniciado. Aguardando tarefas...")

    stop_event = False

    def _handle_signal(signum: int, frame: object) -> None:
        nonlocal stop_event
        logger.info("Sinal %s recebido — encerrando worker...", signum)
        stop_event = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        while not stop_event:
            time.sleep(1)
    finally:
        logger.info("Parando scheduler...")
        _scheduler.stop()
        logger.info("Worker encerrado.")


if __name__ == "__main__":
    main()
