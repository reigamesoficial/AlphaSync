"""
Alembic env.py — Ambiente de migrations para o AlphaSync.

Suporta:
  - migrations online (com engine conectado ao DB)
  - migrations offline (geração de SQL puro)

A URL do banco é extraída do settings (DATABASE_URL via .env).
Os modelos são importados automaticamente para autogenerate.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── path setup ─────────────────────────────────────────────────────────────
# Adiciona o root do projeto ao sys.path para importar app.*
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── importar settings e modelos ─────────────────────────────────────────────
from app.core.config import settings                # noqa: E402
from app.db.connection import Base                  # noqa: E402
from app.db import models  # noqa: F401, E402 — importa todos os models para autogenerate

# ── configuração do alembic ─────────────────────────────────────────────────
config = context.config

# Sobrescreve sqlalchemy.url com o valor real dos settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para autogenerate
target_metadata = Base.metadata


# ── helpers ─────────────────────────────────────────────────────────────────

def include_schemas(name, type_, parent_names, reflected, compare_to):
    """Filtra apenas o schema public (evita pg_catalog etc)."""
    if type_ == "schema":
        return name in (None, "public")
    return True


def run_migrations_offline() -> None:
    """
    Executa migrations em modo offline.
    Gera SQL sem conexão real com o banco.
    Útil para revisar scripts antes de aplicar.

    Uso: alembic upgrade head --sql > migrate.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        include_object=include_schemas,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executa migrations em modo online (conexão real com o banco).
    Modo padrão para: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
