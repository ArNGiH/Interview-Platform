"""create interview feedback table

Revision ID: f42b9a7c63d1
Revises: c7f4a6d2b1e0
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f42b9a7c63d1"
down_revision: Union[str, Sequence[str], None] = "c7f4a6d2b1e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_feedback",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False
        ),
        sa.Column(
            "interview_id",
            sa.UUID(),
            nullable=False
        ),
        sa.Column(
            "report",
            postgresql.JSONB(),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["interview_id"],
            ["interview_sessions.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "interview_id",
            name="uq_interview_feedback_interview_id"
        )
    )


def downgrade() -> None:
    op.drop_table("interview_feedback")
