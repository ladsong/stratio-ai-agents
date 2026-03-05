"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-03-05 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('threads',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('meta', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('graph_registry',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('config', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    
    op.create_table('tool_registry',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('schema', sa.JSON(), nullable=True),
    sa.Column('timeout_ms', sa.Integer(), nullable=True),
    sa.Column('retries', sa.Integer(), nullable=True),
    sa.Column('permission_tag', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    
    op.create_table('knowledge_documents',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('events',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('thread_id', sa.String(length=255), nullable=False),
    sa.Column('idempotency_key', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('idempotency_key')
    )
    
    op.create_table('runs',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('thread_id', sa.String(length=255), nullable=False),
    sa.Column('graph_name', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('knowledge_chunks',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('document_id', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', Vector(1536), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('artifacts',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('run_id', sa.String(length=255), nullable=False),
    sa.Column('artifact_type', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('run_approvals',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('run_id', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=True),
    sa.Column('response', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('tool_calls',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('run_id', sa.String(length=255), nullable=False),
    sa.Column('tool_name', sa.String(length=255), nullable=False),
    sa.Column('inputs', sa.JSON(), nullable=True),
    sa.Column('outputs', sa.JSON(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('tool_calls')
    op.drop_table('run_approvals')
    op.drop_table('artifacts')
    op.drop_table('knowledge_chunks')
    op.drop_table('runs')
    op.drop_table('events')
    op.drop_table('knowledge_documents')
    op.drop_table('tool_registry')
    op.drop_table('graph_registry')
    op.drop_table('threads')
