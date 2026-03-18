"""add_warranties_table

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-17 17:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'warranties',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('appointment_id', sa.Integer(), sa.ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('client_name', sa.String(200), nullable=False),
        sa.Column('client_phone', sa.String(30), nullable=False),
        sa.Column('address_raw', sa.Text(), nullable=True),
        sa.Column('service_description', sa.Text(), nullable=False),
        sa.Column('warranty_period', sa.String(100), nullable=False, server_default='12 meses'),
        sa.Column('warranty_covers', sa.Text(), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_warranties_company', 'warranties', ['company_id'])
    op.create_index('ix_warranties_appointment', 'warranties', ['appointment_id'])


def downgrade() -> None:
    op.drop_index('ix_warranties_appointment', table_name='warranties')
    op.drop_index('ix_warranties_company', table_name='warranties')
    op.drop_table('warranties')
