"""checkpoints table for langgraph

Revision ID: 002
Revises: 001
Create Date: 2026-03-05 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('checkpoints',
    sa.Column('thread_id', sa.String(length=255), nullable=False),
    sa.Column('checkpoint_ns', sa.String(length=255), nullable=False, server_default=''),
    sa.Column('checkpoint_id', sa.String(length=255), nullable=False),
    sa.Column('parent_checkpoint_id', sa.String(length=255), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('checkpoint', sa.JSON(), nullable=False),
    sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id')
    )
    
    op.create_index('idx_checkpoints_thread_id', 'checkpoints', ['thread_id'])
    op.create_index('idx_checkpoints_parent', 'checkpoints', ['parent_checkpoint_id'])


def downgrade() -> None:
    op.drop_index('idx_checkpoints_parent', table_name='checkpoints')
    op.drop_index('idx_checkpoints_thread_id', table_name='checkpoints')
    op.drop_table('checkpoints')
