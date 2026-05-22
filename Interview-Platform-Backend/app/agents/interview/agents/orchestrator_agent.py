import json
from time import perf_counter

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from app.core.logger import logger

from app.agents.interview.prompts import (
    QUESTION_STRATEGY_PROMPT
)

from app.agents.interview.state import (
    InterviewState
)

from app.services.llm_service import (
    get_llm
)

from app.agents.interview.agents.common import (
    compact_for_log,
    state_upper,
    usage_metadata
)


ORCHESTRATOR_AGENT_NAME = "Strategy Orchestrator Agent"

llm = get_llm()


def question_strategy_node(
    state: InterviewState
):

    started_at = perf_counter()

    candidate_evaluation = state.get(
        "candidate_evaluation",
        {}
    )

    evaluation_text = (
        candidate_evaluation.get(
            "evaluation",
            ""
        )
    )

    previous_question = (
        candidate_evaluation.get(
            "question",
            ""
        )
    )

    candidate_answer = (
        candidate_evaluation.get(
            "answer",
            ""
        )
    )

    prompt = QUESTION_STRATEGY_PROMPT.format(
        interview_role=state.get(
            "interview_role",
            "Software Engineer"
        ),
        experience_level=state.get(
            "experience_level",
            "mid-level"
        ),
        interview_type=state_upper(
            state,
            "interview_type",
            "technical"
        ),
        requested_difficulty=state_upper(
            state,
            "difficulty",
            "medium"
        ),
        question_count=state.get(
            "question_count",
            0
        ),
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        evaluation=evaluation_text
    )

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=prompt
                ),
                HumanMessage(
                    content=(
                        "Determine the next "
                        "interview strategy."
                    )
                )
            ]
        )

    except Exception:

        logger.exception(
            (
                "question_strategy_generation_failed "
                "question_count=%s"
            ),
            state.get(
                "question_count",
                0
            )
        )

        raise

    strategy_response = json.loads(
        response.content
    )

    state["question_strategy"] = strategy_response

    logger.info(
        (
            "question_strategy_generated "
            "question_count=%s "
            "strategy_type=%s "
            "user_intent=%s "
            "difficulty_level=%s "
            "should_explain=%s "
            "should_end_interview=%s "
            "duration_ms=%s "
            "usage=%s "
            "output=%s"
        ),
        state.get(
            "question_count",
            0
        ),
        strategy_response.get(
            "strategy_type"
        ),
        strategy_response.get(
            "user_intent"
        ),
        strategy_response.get(
            "difficulty_level"
        ),
        strategy_response.get(
            "should_explain"
        ),
        strategy_response.get(
            "should_end_interview"
        ),
        int((perf_counter() - started_at) * 1000),
        usage_metadata(response),
        compact_for_log(
            response.content
        )
    )

    return state
