from __future__ import annotations

import json
import logging
import logging.config
import sys
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.connection import Base, engine
from app.db import models  # noqa: F401


# ─── Logging setup ─────────────────────────────────────────────────────────────
class _JsonFormatter(logging.Formatter):
    """Formata logs como JSON estruturado para produção."""

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


def _configure_logging() -> None:
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


_configure_logging()
logger = logging.getLogger("alphasync")


# ─── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    debug=settings.app_debug,
)


# ─── CORS middleware ───────────────────────────────────────────────────────────
_cors = settings.cors_origins_list
_allow_all = _cors == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ─── Request-ID middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.api_v1_prefix)


# ─── Health endpoints ─────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health():
    """
    Healthcheck básico — usado por load balancers e containers.
    Retorna 200 se o servidor está de pé.
    """
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": settings.app_version,
    }


@app.get("/health/full", tags=["health"])
def health_full():
    """
    Healthcheck completo — verifica DB e Redis.
    Retorna 200 se todos os serviços críticos estão saudáveis.
    """
    from app.db.connection import engine as _engine
    from app.core.redis_client import redis_health
    import sqlalchemy

    # DB check
    db_status: dict
    try:
        with _engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        db_status = {"status": "ok"}
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        db_status = {"status": "unavailable", "error": str(exc)}

    # Redis check
    redis_status = redis_health()

    overall = (
        "ok"
        if db_status["status"] == "ok" and redis_status["status"] == "ok"
        else "degraded"
    )

    return JSONResponse(
        status_code=200 if overall == "ok" else 207,
        content={
            "status": overall,
            "env": settings.app_env,
            "version": settings.app_version,
            "services": {
                "database": db_status,
                "redis": redis_status,
            },
        },
    )


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    _t0 = time.monotonic()

    # 1. Criar tabelas (dev) / verificar (prod — preferir Alembic)
    Base.metadata.create_all(bind=engine)
    _tables = len(Base.metadata.tables)

    # 2. Sincronizar DomainDefinitions builtin
    try:
        from sqlalchemy.orm import Session as _Session
        from app.services.domain_definition_service import DomainDefinitionService as _DDS
        with _Session(engine) as _db:
            _result = _DDS(_db).sync_builtin_domains()
            _created = _result["created"]
            _skipped = _result["skipped"]
            logger.info(f"  Domínios  : {_created} criados, {_skipped} já existentes")
    except Exception as _exc:
        logger.warning(f"  Domínios  : sync falhou — {_exc}")

    # 3. Contar rotas registradas
    _routes = sum(1 for r in app.routes if hasattr(r, "methods"))

    # 4. Banner de startup
    _elapsed = (time.monotonic() - _t0) * 1000
    _bar = "=" * 60

    logger.info(_bar)
    logger.info(f"  {settings.app_name} v{settings.app_version} — startup")
    logger.info(_bar)
    logger.info(f"  Ambiente  : {settings.app_env.upper()}")
    logger.info(f"  Debug     : {settings.app_debug}")
    logger.info(f"  Log level : {settings.log_level}")
    logger.info(f"  API prefix: {settings.api_v1_prefix}")
    logger.info(f"  DB tabelas: {_tables}")
    logger.info(f"  Rotas HTTP: {_routes}")

    _cors_display = (
        "TODAS AS ORIGENS (*)"
        if _allow_all
        else ", ".join(_cors) or "nenhuma"
    )
    logger.info(f"  CORS      : {_cors_display}")
    logger.info(f"  Database  : {settings.masked_database_url}")

    if not settings.is_production:
        logger.info("  Docs      : /docs  |  /redoc")

    _warn_fragments = {"change_this", "changeme", "placeholder"}
    if any(f in settings.secret_key.lower() for f in _warn_fragments):
        logger.warning(
            "  SECRET_KEY parece ser um placeholder. "
            "Gere uma chave real antes de ir para produção."
        )

    logger.info(f"  Pronto em : {_elapsed:.1f} ms")
    logger.info(_bar)

    # 5. Iniciar scheduler de tarefas periódicas (lembretes, etc.)
    # Em deploy distribuído, ENABLE_SCHEDULER=false no app — roda só na VPS worker.
    if settings.enable_scheduler:
        try:
            from app.core import scheduler as _scheduler
            _scheduler.start()
        except Exception as _exc:
            logger.warning(f"  Scheduler : não iniciado — {_exc}")
    else:
        logger.info("  Scheduler : desabilitado (ENABLE_SCHEDULER=false)")


@app.on_event("shutdown")
def on_shutdown():
    if settings.enable_scheduler:
        try:
            from app.core import scheduler as _scheduler
            _scheduler.stop()
        except Exception:
            pass
