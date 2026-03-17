"""add_reminder_status_skipped_failed

Revision ID: c978f46cdd18
Revises: fa84cb3985c3
Create Date: 2026-03-17 15:52:32.359601+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c978f46cdd18'
down_revision: Union[str, None] = 'fa84cb3985c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE reminder_status_enum ADD VALUE IF NOT EXISTS 'skipped'")
    op.execute("ALTER TYPE reminder_status_enum ADD VALUE IF NOT EXISTS 'failed'")


def downgrade() -> None:
    pass
