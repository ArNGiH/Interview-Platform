from typing import TypedDict
from typing import List
from typing import Optional
from typing import Any


class InterviewState(TypedDict):

    interview_id: str
    resume_id: str | None
    system_prompt: str
    messages: List[dict]
    retrieved_chunks: List[str]
    latest_user_message: Optional[str]
    current_question: Optional[str]
    question_count: int
    interview_role: str
    experience_level: str
    interview_type: str