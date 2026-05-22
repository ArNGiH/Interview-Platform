import uuid

from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class InterviewFeedback(Base):

    __tablename__ = "interview_feedback"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    interview_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False
    )

    report = Column(
        JSONB,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "interview_id",
            name="uq_interview_feedback_interview_id"
        ),
    )
