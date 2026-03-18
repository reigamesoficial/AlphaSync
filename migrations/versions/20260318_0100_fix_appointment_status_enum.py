"""fix_appointment_status_enum

Adiciona os valores corretos (lowercase) ao enum de status de appointments.
A tabela está vazia, então é seguro recriar o tipo.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-03-18 01:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Convert status column to plain text so we can drop the enum type
    op.execute("ALTER TABLE appointments ALTER COLUMN status TYPE text")

    # 2. Drop the old enum with wrong uppercase values
    op.execute("DROP TYPE IF EXISTS appointment_status_enum")

    # 3. Create new enum with correct lowercase values (all statuses the app uses)
    op.execute("""
        CREATE TYPE appointment_status_enum AS ENUM (
            'scheduled',
            'in_progress',
            'completed',
            'confirmed',
            'done',
            'rescheduled',
            'cancelled',
            'abandoned'
        )
    """)

    # 4. Restore column as enum. Table is empty so no row conversion is needed.
    op.execute("""
        ALTER TABLE appointments
        ALTER COLUMN status TYPE appointment_status_enum
        USING status::appointment_status_enum
    """)

    # 5. Restore the NOT NULL default
    op.execute(
        "ALTER TABLE appointments ALTER COLUMN status SET DEFAULT 'scheduled'::appointment_status_enum"
    )


def downgrade() -> None:
    # Restore to original uppercase enum (best effort)
    op.execute("ALTER TABLE appointments ALTER COLUMN status TYPE text")
    op.execute("DROP TYPE IF EXISTS appointment_status_enum")
    op.execute("""
        CREATE TYPE appointment_status_enum AS ENUM (
            'SCHEDULED', 'CONFIRMED', 'CANCELLED', 'DONE', 'RESCHEDULED'
        )
    """)
    op.execute("""
        ALTER TABLE appointments
        ALTER COLUMN status TYPE appointment_status_enum
        USING 'SCHEDULED'::appointment_status_enum
    """)
