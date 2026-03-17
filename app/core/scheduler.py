"""
AlphaSync — Scheduler interno de tarefas periódicas.

Usa threading para rodar tarefas em background sem dependências externas.
Tarefas configuradas:
  - check_reminders: a cada 30 min — envia lembretes de agendamento 24h antes.

Como parar: chame scheduler.stop() no evento de shutdown do FastAPI.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger("alphasync.scheduler")

_REMINDER_INTERVAL_SECONDS = 30 * 60  # 30 minutos


class _RepeatingTimer:
    """Timer que re-agenda a si mesmo até ser cancelado."""

    def __init__(self, interval: float, fn: Callable, name: str = "timer") -> None:
        self._interval = interval
        self._fn = fn
        self._name = name
        self._timer: threading.Timer | None = None
        self._stopped = threading.Event()

    def start(self) -> None:
        self._stopped.clear()
        self._schedule()
        logger.info("Scheduler '%s' iniciado (intervalo: %ss)", self._name, self._interval)

    def stop(self) -> None:
        self._stopped.set()
        if self._timer:
            self._timer.cancel()
        logger.info("Scheduler '%s' parado.", self._name)

    def _schedule(self) -> None:
        if self._stopped.is_set():
            return
        self._timer = threading.Timer(self._interval, self._run)
        self._timer.daemon = True
        self._timer.name = self._name
        self._timer.start()

    def _run(self) -> None:
        if self._stopped.is_set():
            return
        try:
            self._fn()
        except Exception as exc:
            logger.error("Scheduler '%s' erro na execução: %s", self._name, exc)
        finally:
            self._schedule()


def _run_reminders() -> None:
    from app.db.connection import SessionLocal
    from app.services.reminder_service import send_pending_reminders

    logger.debug("Scheduler: verificando lembretes pendentes (%s)", datetime.now(timezone.utc).isoformat())
    db = SessionLocal()
    try:
        stats = send_pending_reminders(db)
        if stats["sent"] or stats["failed"]:
            logger.info("Lembretes: %s", stats)
    finally:
        db.close()


_reminder_timer = _RepeatingTimer(
    interval=_REMINDER_INTERVAL_SECONDS,
    fn=_run_reminders,
    name="reminder_check",
)


def start() -> None:
    _reminder_timer.start()


def stop() -> None:
    _reminder_timer.stop()
