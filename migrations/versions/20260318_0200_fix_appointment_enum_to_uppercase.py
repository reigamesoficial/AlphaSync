"""fix_appointment_enum_to_uppercase

SQLAlchemy uses enum member NAMES (uppercase) as DB values by default.
The previous migration incorrectly stored lowercase values.
This corrects the PostgreSQL enum to use uppercase values matching SQLAlchemy's behavior.
Table is empty so no data migration is needed.

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-03-18 02:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop the column default first (it depends on the enum type)
    op.execute("ALTER TABLE appointments ALTER COLUMN status DROP DEFAULT")
    # 2. Convert column to text so we can drop the enum type
    op.execute("ALTER TABLE appointments ALTER COLUMN status TYPE text")
    # 3. Drop incorrect lowercase enum
    op.execute("DROP TYPE IF EXISTS appointment_status_enum")
    # 4. Create correct uppercase enum (SQLAlchemy default: uses NAMES not .values)
    op.execute("""
        CREATE TYPE appointment_status_enum AS ENUM (
            'SCHEDULED',
            'IN_PROGRESS',
            'COMPLETED',
            'CONFIRMED',
            'DONE',
            'RESCHEDULED',
            'CANCELLED',
            'ABANDONED'
        )
    """)
    # 5. Restore column as enum (table is empty, USING is safe)
    op.execute("""
        ALTER TABLE appointments
        ALTER COLUMN status TYPE appointment_status_enum
        USING COALESCE(NULLIF(status, ''), 'SCHEDULED')::appointment_status_enum
    """)
    # 6. Restore NOT NULL default
    op.execute(
        "ALTER TABLE appointments ALTER COLUMN status SET DEFAULT 'SCHEDULED'::appointment_status_enum"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE appointments ALTER COLUMN status TYPE text")
    op.execute("DROP TYPE IF EXISTS appointment_status_enum")
    op.execute("""
        CREATE TYPE appointment_status_enum AS ENUM (
            'scheduled', 'in_progress', 'completed', 'confirmed',
            'done', 'rescheduled', 'cancelled', 'abandoned'
        )
    """)
    op.execute("""
        ALTER TABLE appointments
        ALTER COLUMN status TYPE appointment_status_enum
        USING 'scheduled'::appointment_status_enum
    """)
