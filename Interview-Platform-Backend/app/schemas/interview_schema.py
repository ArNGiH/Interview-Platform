from pydantic import BaseModel
from uuid import UUID

class ChatRequest(BaseModel):
    message: str

class InterviewSetupRequest(BaseModel):
    role: str
    experience_level: str
    difficulty: str
    interview_type: str
    interview_mode: str
    resume_id: str | None = None
    resume_uploaded: bool
    job_description_provided: bool


class InterviewChatRequest(BaseModel):
    interview_id: UUID
    user_message: str


class StartInterviewRequest(BaseModel):

    interview_id: UUID