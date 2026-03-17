"""fix_reminder_status_uppercase

Revision ID: d1e2f3a4b5c6
Revises: c978f46cdd18
Create Date: 2026-03-17 16:30:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c978f46cdd18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE reminder_status_enum ADD VALUE IF NOT EXISTS 'SKIPPED'")
    op.execute("ALTER TYPE reminder_status_enum ADD VALUE IF NOT EXISTS 'FAILED'")


def downgrade() -> None:
    pass
