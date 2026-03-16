"""
Redis client — conexão singleton com pool de conexões.

Uso:
  from app.core.redis_client import get_redis, redis_health

  r = get_redis()
  r.set("key", "value", ex=60)
  val = r.get("key")
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger("alphasync.redis")

try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


class RedisUnavailableError(Exception):
    """Raised when Redis is not reachable and operation is critical."""


@lru_cache(maxsize=1)
def _build_pool(redis_url: str) -> "_redis_lib.ConnectionPool":
    return _redis_lib.ConnectionPool.from_url(
        redis_url,
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=False,
    )


def get_redis(redis_url: str | None = None) -> "_redis_lib.Redis":
    """
    Retorna cliente Redis conectado via pool.
    Importa a URL do settings se não fornecida.
    """
    if not _REDIS_AVAILABLE:
        raise RedisUnavailableError("Biblioteca redis não instalada.")

    if redis_url is None:
        from app.core.config import settings
        redis_url = settings.redis_url

    pool = _build_pool(redis_url)
    return _redis_lib.Redis(connection_pool=pool)


def redis_health() -> dict:
    """
    Verifica conexão com Redis e retorna status de saúde.
    Nunca lança exceção — retorna status 'unavailable' em falha.
    """
    if not _REDIS_AVAILABLE:
        return {"status": "unavailable", "error": "redis lib not installed"}

    try:
        r = get_redis()
        latency_ms = _ping_with_latency(r)
        info = r.info("server")
        return {
            "status": "ok",
            "latency_ms": latency_ms,
            "version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", -1),
        }
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return {"status": "unavailable", "error": str(exc)}


def _ping_with_latency(r: "_redis_lib.Redis") -> float:
    import time
    t0 = time.monotonic()
    r.ping()
    return round((time.monotonic() - t0) * 1000, 2)


# ── Helpers simples de cache ────────────────────────────────────────────────

def cache_get(key: str, default: Optional[str] = None) -> Optional[str]:
    """Lê valor do cache. Retorna default em caso de falha."""
    try:
        val = get_redis().get(key)
        return val if val is not None else default
    except Exception:
        return default


def cache_set(key: str, value: str, ttl_seconds: int = 300) -> bool:
    """Salva valor no cache com TTL em segundos. Retorna False em falha."""
    try:
        get_redis().set(key, value, ex=ttl_seconds)
        return True
    except Exception:
        return False


def cache_delete(key: str) -> bool:
    """Remove chave do cache. Retorna False em falha."""
    try:
        get_redis().delete(key)
        return True
    except Exception:
        return False
