"""add pinned field to conversations

Revision ID: 0002_add_pinned_to_conversations
Revises: 0001_initial
Create Date: 2025-01-27 12:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_add_pinned_to_conversations'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('pinned', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('conversations', 'pinned')
