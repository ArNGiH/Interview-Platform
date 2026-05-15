from typing import TypedDict
from typing import List
from typing import Optional


class InterviewState(TypedDict):
    interview_id: str
    system_prompt: str
    messages: List[dict]
    retrieved_chunks: List[str]
    latest_user_message: Optional[str]
    current_question: Optional[str]
    question_count: int