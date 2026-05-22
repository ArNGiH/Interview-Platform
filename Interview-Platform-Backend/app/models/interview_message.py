import uuid

from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey

from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

from app.models.interview_session import InterviewSession


class InterviewMessage(Base):

    __tablename__ = "interview_messages"

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

    role = Column(
        String,
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )