#!/usr/bin/env python3
"""
scripts/seed_admin.py
─────────────────────
Cria o primeiro usuário admin da plataforma caso ainda não exista.
Idempotente: não duplica dados se já executado.

Uso:
    python scripts/seed_admin.py

Variáveis de ambiente (opcionais — têm defaults para dev):
    SEED_ADMIN_EMAIL      email do admin          (padrão: admin@alphasync.app)
    SEED_ADMIN_PASSWORD   senha do admin          (padrão: changeme123)
    SEED_ADMIN_NAME       nome do admin           (padrão: Admin)
    SEED_COMPANY_SLUG     slug da empresa         (padrão: default)
    SEED_COMPANY_NAME     nome da empresa         (padrão: AlphaSync)
"""

import sys
import os
import logging

# Garante que o diretório raiz do projeto esteja no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import hash_password
from app.db.connection import Base, engine, SessionLocal
from app.db import models  # noqa — registra os models no metadata
from app.db.models import (
    Company,
    CompanySettings,
    CompanyStatus,
    ServiceDomain,
    User,
    UserRole,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("seed_admin")

SEP = "─" * 60


def main() -> None:
    logger.info(SEP)
    logger.info("  AlphaSync — Seed do primeiro admin")
    logger.info(SEP)

    # 1. Garante que as tabelas existam
    Base.metadata.create_all(bind=engine)
    logger.info("  ✅ Tabelas verificadas/criadas")

    db = SessionLocal()
    try:
        email = settings.seed_admin_email
        password = settings.seed_admin_password
        name = settings.seed_admin_name
        slug = settings.seed_company_slug
        company_name = settings.seed_company_name

        logger.info(f"  Email     : {email}")
        logger.info(f"  Empresa   : {company_name} (slug: {slug})")

        # 2. Verifica se admin já existe
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.info(f"  ⚠️  Usuário '{email}' já existe (id={existing_user.id}). Nada foi alterado.")
            logger.info(SEP)
            return

        # 3. Verifica/cria a empresa
        company = db.query(Company).filter(Company.slug == slug).first()
        if not company:
            company = Company(
                slug=slug,
                name=company_name,
                status=CompanyStatus.ACTIVE,
                service_domain=ServiceDomain.PROTECTION_NETWORK,
                is_active=True,
            )
            db.add(company)
            db.flush()
            logger.info(f"  ✅ Empresa criada: '{company_name}' (id={company.id})")

            # CompanySettings
            cs = CompanySettings(
                company_id=company.id,
                bot_name="AlphaBot",
                currency="BRL",
                timezone="America/Sao_Paulo",
                extra_settings={
                    "pricing_rules": {
                        "default_price_per_m2": 45.0,
                        "minimum_order_value": 150.0,
                        "visit_fee": 0.0,
                        "mesh_price_overrides": {"3x3": 50.0, "5x5": 40.0},
                    },
                    "network_colors": ["branca", "preta", "areia", "cinza"],
                    "available_mesh_types": ["3x3", "5x5"],
                },
            )
            db.add(cs)
            db.flush()
            logger.info(f"  ✅ Configurações da empresa criadas")
        else:
            logger.info(f"  ℹ️  Empresa '{slug}' já existe (id={company.id})")

        # 4. Cria o usuário admin
        pw_hash = hash_password(password)
        admin = User(
            company_id=company.id,
            email=email,
            password_hash=pw_hash,
            role=UserRole.COMPANY_ADMIN,
            name=name,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        logger.info(SEP)
        logger.info(f"  ✅ Admin criado com sucesso!")
        logger.info(f"     Email : {email}")
        logger.info(f"     Senha : {password}")
        logger.info(f"     Role  : {UserRole.COMPANY_ADMIN.value}")
        logger.info(f"     Empresa: {company_name} (id={company.id})")

        if any(w in password.lower() for w in ["change", "123", "senha", "pass"]):
            logger.warning(
                "  ⚠️  A senha parece fraca. Altere-a via API após o primeiro login."
            )
        logger.info(SEP)

    except Exception as exc:
        db.rollback()
        logger.error(f"  ❌ Erro ao executar seed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
