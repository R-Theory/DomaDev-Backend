"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-11 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('conversation_id', sa.String(length=32), nullable=False),
        sa.Column('parent_id', sa.String(length=32), nullable=True),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_json', sa.JSON(), nullable=True),
        sa.Column('model', sa.String(length=200), nullable=True),
        sa.Column('model_key', sa.String(length=64), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('temperature', sa.Integer(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('upstream_id', sa.String(length=100), nullable=True),
        sa.Column('raw_request_gzip', sa.LargeBinary(), nullable=True),
        sa.Column('raw_response_gzip', sa.LargeBinary(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_conversation', 'messages', ['conversation_id'], unique=False)
    op.create_index('ix_messages_started_at', 'messages', ['started_at'], unique=False)

    op.create_table(
        'message_streams',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('message_id', sa.String(length=32), nullable=False),
        sa.Column('raw_sse_gzip', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('message_streams')
    op.drop_index('ix_messages_started_at', table_name='messages')
    op.drop_index('ix_messages_conversation', table_name='messages')
    op.drop_table('messages')
    op.drop_table('conversations')


