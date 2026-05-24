from typing import TypedDict
from typing import List
from typing import Optional

from app.agents.interview.schemas import (
    CandidateEvaluationOutput,
    QuestionStrategyOutput,
    ResumeAnalysisOutput,
)


class InterviewState(TypedDict):

    interview_id: str
    resume_id: str | None
    system_prompt: str

    messages: List[dict]

    current_topic: str | None
    topic_history: List[str]

    candidate_confidence: str | None
    candidate_conduct: str | None
    interview_phase: str | None

    retrieved_chunks: List[str]

    resume_analysis: ResumeAnalysisOutput | None

    latest_user_message: Optional[str]

    current_question: Optional[str]

    question_count: int

    candidate_evaluation: CandidateEvaluationOutput | None

    question_strategy: QuestionStrategyOutput | None

    interview_role: str
    experience_level: str
    interview_type: str
    interview_mode: str | None
    difficulty: str

    streaming_prompt: str | None
    streaming_instruction: str | None