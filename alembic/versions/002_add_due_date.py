"""add due_date to tasks

Revision ID: 002
Revises: 001
Create Date: 2025-06-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("tasks", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column("tasks", "due_date")
