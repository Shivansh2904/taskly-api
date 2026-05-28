"""add comments table

Revision ID: 003
Revises: 002
Create Date: 2026-05-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "task_id",
            sa.Integer,
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_comments_task_id", "comments", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_task_id", table_name="comments")
    op.drop_table("comments")
