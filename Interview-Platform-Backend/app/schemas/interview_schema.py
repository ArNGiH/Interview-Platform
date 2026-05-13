from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class InterviewSetupRequest(BaseModel):
    role: str
    experience_level: str
    difficulty: str
    interview_type: str
    interview_mode: str
    resume_uploaded: bool
    job_description_provided: bool