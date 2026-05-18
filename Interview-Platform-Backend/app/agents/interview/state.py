from typing import TypedDict
from typing import List
from typing import Optional
from typing import Literal
from typing import Any

class StrategyOutput(TypedDict):
    strategy_type: Literal[
        "FOLLOW_UP",
        "DEEPER_TECHNICAL",
        "NEW_TOPIC",
        "CLARIFICATION",
        "SYSTEM_DESIGN",
        "EASIER_QUESTION",
        "END_INTERVIEW"
    ]
    user_intent: Literal[
        "ANSWER_QUESTION",
        "ASKING_CLARIFICATION",
        "DOES_NOT_KNOW",
        "PARTIAL_ANSWER",
        "STRONG_ANSWER",
        "WEAK_ANSWER",
        "ENDING_INTERVIEW"
    ]
    difficulty_level: Literal[
        "EASY",
        "MEDIUM",
        "HARD"
    ]
    should_explain: bool
    should_continue_topic: bool
    should_end_interview: bool
    next_topic: Optional[str]
    reasoning: str
    next_node: str  
    topic: str | None
    candidate_confidence: str | None
    candidate_conduct: str | None
    interview_phase: str | None

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
    latest_user_message: Optional[str]
    current_question: Optional[str]
    question_count: int
    candidate_evaluation: dict | None
    question_strategy: StrategyOutput | None
    interview_role: str
    experience_level: str
    interview_type: str