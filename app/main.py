from __future__ import annotations

import logging
import logging.config
import sys
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.connection import Base, engine
from app.db import models  # noqa: F401


# ─── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("alphasync")


# ─── App factory ──────────────────────────────────────────────────────────────
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


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.api_v1_prefix)


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "env": settings.app_env, "version": settings.app_version}


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    _t0 = time.monotonic()

    # 1. Criar tabelas
    Base.metadata.create_all(bind=engine)
    _tables = len(Base.metadata.tables)

    # 2. Contar rotas registradas
    _routes = sum(1 for r in app.routes if hasattr(r, "methods"))

    # 3. Banner de startup
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
        logger.info(f"  Docs      : /docs  |  /redoc")

    _warn_fragments = {"change_this", "changeme", "placeholder"}
    if any(f in settings.secret_key.lower() for f in _warn_fragments):
        logger.warning(
            "  SECRET_KEY parece ser um placeholder. "
            "Gere uma chave real antes de ir para produção."
        )

    logger.info(f"  Pronto em : {_elapsed:.1f} ms")
    logger.info(_bar)
