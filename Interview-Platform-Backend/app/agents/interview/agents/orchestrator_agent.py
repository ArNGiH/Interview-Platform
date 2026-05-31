from time import perf_counter

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)
from app.services.langfuse_service import (
    agent_observation
)

from app.core.logger import logger

from app.agents.interview.prompts import (
    QUESTION_STRATEGY_PROMPT
)

from app.agents.interview.state import (
    InterviewState
)

from app.agents.interview.schemas import (
    QuestionStrategyOutput
)

from app.services.llm_service import (
    get_llm
)

from app.agents.interview.agents.common import (
    compact_for_log,
    model_dump_for_prompt,
    normalize_structured_output,
    state_upper,
    structured_get
)


ORCHESTRATOR_AGENT_NAME = "Strategy Orchestrator Agent"

llm = get_llm()
structured_llm = llm.with_structured_output(
    QuestionStrategyOutput
)


def question_strategy_node(
    state: InterviewState
):

    started_at = perf_counter()

    candidate_evaluation = state.get(
        "candidate_evaluation",
    )

    evaluation_text = (
        structured_get(candidate_evaluation, "summary", "")
    )

    previous_question = (
        structured_get(candidate_evaluation, "question", "")
    )

    candidate_answer = (
        structured_get(candidate_evaluation, "answer", "")
    )

    resume_analysis = state.get(
        "resume_analysis"
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
        resume_analysis=model_dump_for_prompt(
            resume_analysis
        ),
        question_count=state.get(
            "question_count",
            0
        ),
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        evaluation=evaluation_text
    )

    with agent_observation(
        name="Question Strategy",
        input_data={
            "interview_role": state.get(
                "interview_role",
                "Software Engineer"
            ),
            "experience_level": state.get(
                "experience_level",
                "mid-level"
            ),
            "interview_type": state.get(
                "interview_type",
                "technical"
            ),
            "difficulty": state.get(
                "difficulty",
                "medium"
            ),
            "question_count": state.get(
                "question_count",
                0
            ),
            "previous_question": previous_question,
            "candidate_answer": candidate_answer,
            "evaluation": evaluation_text
        }
    ) as observation:

        try:

            raw_strategy_response = structured_llm.invoke(
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

            strategy_response = (
                normalize_structured_output(
                    raw_strategy_response,
                    QuestionStrategyOutput
                )
            )

            observation.update(
                output=strategy_response.model_dump()
            )
            observation.end()

        except Exception as ex:


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

    state["question_strategy"] = (
        strategy_response
    )

    logger.info(
        (
            "question_strategy_generated "
            "question_count=%s "
            "strategy_type=%s "
            "user_intent=%s "
            "difficulty_level=%s "
            "should_explain=%s "
            "should_end_interview=%s "
            "next_node=%s "
            "duration_ms=%s "
            "output=%s"
        ),
        state.get(
            "question_count",
            0
        ),
        strategy_response.strategy_type,
        strategy_response.user_intent,
        strategy_response.difficulty_level,
        strategy_response.should_explain,
        strategy_response.should_end_interview,
        strategy_response.next_node,
        int(
            (
                perf_counter()
                - started_at
            ) * 1000
        ),
        compact_for_log(
            str(
                strategy_response.model_dump()
            )
        )
    )

    return state