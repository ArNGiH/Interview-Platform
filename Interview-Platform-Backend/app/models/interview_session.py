import uuid

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.user import User

from datetime import datetime

from app.core.database import Base


class InterviewSession(Base):

    __tablename__ = "interview_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("users.id"),
    nullable=False
)

    role = Column(String, nullable=False)

    resume_id = Column(
    UUID(as_uuid=True),
    ForeignKey("resumes.id"),
    nullable=True
)

    experience_level = Column(String, nullable=False)

    difficulty = Column(String, nullable=False)

    interview_type = Column(String, nullable=False)

    interview_mode = Column(String, nullable=False)

    resume_uploaded = Column(Boolean, default=False)

    job_description_provided = Column(Boolean, default=False)

    system_prompt = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)