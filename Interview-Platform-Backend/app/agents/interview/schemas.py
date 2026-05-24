from typing import List, Literal

from pydantic import BaseModel, Field


StrategyType = Literal[
    "FOLLOW_UP",
    "DEEPER_TECHNICAL",
    "NEW_TOPIC",
    "CLARIFICATION",
    "SYSTEM_DESIGN",
    "EASIER_QUESTION",
    "END_INTERVIEW",
    "CONDUCT_WARNING",
]

UserIntent = Literal[
    "ANSWER_QUESTION",
    "ASKING_CLARIFICATION",
    "DOES_NOT_KNOW",
    "PARTIAL_ANSWER",
    "STRONG_ANSWER",
    "WEAK_ANSWER",
    "ENDING_INTERVIEW",
    "HOSTILE_BEHAVIOR",
]

DifficultyLevel = Literal[
    "EASY",
    "MEDIUM",
    "HARD",
]

CandidateConfidence = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
]

CandidateConduct = Literal[
    "PROFESSIONAL",
    "FRUSTRATED",
    "HOSTILE",
]

InterviewPhase = Literal[
    "INTRODUCTION",
    "RESUME_DISCUSSION",
    "TECHNICAL_SCREENING",
    "DEEP_DIVE",
    "SYSTEM_DESIGN",
    "BEHAVIORAL",
    "WRAP_UP",
    "TERMINATED",
]

InterviewNodeName = Literal[
    "clarification_node",
    "easier_question_node",
    "deep_technical_node",
    "topic_transition_node",
    "system_design_node",
    "conduct_warning_node",
    "end_interview_node",
    "default_question_node",
]

HiringRecommendation = Literal[
    "STRONG_NO",
    "NO",
    "LEAN_NO",
    "LEAN_YES",
    "YES",
    "STRONG_YES",
]


class ResumeAnalysisOutput(BaseModel):

    primary_skills: List[str]
    secondary_skills: List[str]
    probable_seniority: str
    project_domains: List[str]
    strengths: List[str]
    weak_signal_areas: List[str]
    suggested_interview_topics: List[str]


class CandidateEvaluationOutput(BaseModel):
    question: str = Field(
        description="The interviewer question being evaluated."
    )
    answer: str = Field(
        description="The candidate answer being evaluated."
    )
    summary: str = Field(
        description="Concise orchestration-focused evaluation summary."
    )
    answer_relevance: str
    communication_clarity: str
    depth_of_reflection: str
    confidence: CandidateConfidence
    user_intent: UserIntent
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    should_reduce_difficulty: bool = False
    should_probe_deeper: bool = False


class QuestionStrategyOutput(BaseModel):
    strategy_type: StrategyType
    user_intent: UserIntent
    difficulty_level: DifficultyLevel
    should_explain: bool
    should_continue_topic: bool
    should_end_interview: bool
    next_topic: str | None = None
    candidate_confidence: CandidateConfidence | None = None
    candidate_conduct: CandidateConduct | None = None
    interview_phase: InterviewPhase | None = None
    next_node: InterviewNodeName
    reasoning: str



class FeedbackAgentVotes(BaseModel):
    technical_interviewer: str
    behavioral_interviewer: str
    hiring_manager: str


class FeedbackReportOutput(BaseModel):
    overall_summary: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    communication_score: int = Field(ge=0, le=10)
    technical_score: int = Field(ge=0, le=10)
    behavioral_score: int = Field(ge=0, le=10)
    confidence_level: CandidateConfidence
    hiring_recommendation: HiringRecommendation
    recommendation_reason: str
    improvement_roadmap: List[str] = Field(default_factory=list)
    agent_votes: FeedbackAgentVotes
