"""add status to interview sessions

Revision ID: c7f4a6d2b1e0
Revises: 794e8399aca0
Create Date: 2026-05-20 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7f4a6d2b1e0"
down_revision: Union[str, Sequence[str], None] = "794e8399aca0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="active"
        )
    )


def downgrade() -> None:
    op.drop_column(
        "interview_sessions",
        "status"
    )
