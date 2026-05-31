from time import perf_counter

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from app.core.logger import logger

from app.agents.interview.prompts import (
    FOLLOWUP_EVALUATION_PROMPT,
    BEHAVIORAL_EVALUATION_PROMPT
)

from app.agents.interview.state import (
    InterviewState
)

from app.agents.interview.schemas import (
    CandidateEvaluationOutput
)

from app.services.llm_service import (
    get_llm
)

from app.services.langfuse_service import (
    agent_observation
)

from app.agents.interview.agents.common import (
    compact_for_log,
    is_behavioral_interview,
    normalize_structured_output,
)


EVALUATION_AGENT_NAME = "Evaluation Agent"

llm = get_llm()

structured_llm = llm.with_structured_output(
    CandidateEvaluationOutput
)


def evaluate_candidate_answer_node(
    state: InterviewState
):

    started_at = perf_counter()

    latest_user_message = state.get(
        "latest_user_message",
        ""
    )

    messages = state.get(
        "messages",
        []
    )

    previous_question = ""

    for message in reversed(messages):

        if message["role"] == "assistant":

            previous_question = (
                message["content"]
            )

            break

    evaluation_prompt = (
        BEHAVIORAL_EVALUATION_PROMPT
        if is_behavioral_interview(state)
        else FOLLOWUP_EVALUATION_PROMPT
    )

    prompt = f"""
    {evaluation_prompt}

    Interview Type:
    {state.get("interview_type", "technical")}

    Requested Difficulty:
    {state.get("difficulty", "medium")}

    Interviewer Question:
    {previous_question}

    Candidate Answer:
    {latest_user_message}

    Analyze the candidate response.
    """

    with agent_observation(
        name="Candidate Evaluation",
        input_data={
            "interview_type": state.get(
                "interview_type",
                "technical"
            ),
            "difficulty": state.get(
                "difficulty",
                "medium"
            ),
            "previous_question": previous_question,
            "candidate_answer": latest_user_message,
        }
    ) as observation:

        try:

            raw_response = structured_llm.invoke(
                [
                    SystemMessage(
                        content=prompt
                    ),
                    HumanMessage(
                        content=(
                            "Evaluate the candidate response."
                        )
                    )
                ]
            )

            response = normalize_structured_output(
                raw_response,
                CandidateEvaluationOutput
            )

            observation.update(
                output=response.model_dump()
            )
            observation.end()

        except Exception as ex:

            logger.exception(
                (
                    "candidate_answer_evaluation_failed "
                    "question_count=%s"
                ),
                state.get(
                    "question_count",
                    0
                )
            )

            raise

    evaluation = response.model_copy(
        update={
            "question": previous_question,
            "answer": latest_user_message
        }
    )

    state["candidate_evaluation"] = (
        evaluation
    )

    logger.info(
        (
            "candidate_answer_evaluated "
            "question_count=%s "
            "confidence=%s "
            "user_intent=%s "
            "needs_clarification=%s "
            "should_probe_deeper=%s "
            "duration_ms=%s "
            "evaluation=%s"
        ),
        state.get(
            "question_count",
            0
        ),
        evaluation.confidence,
        evaluation.user_intent,
        evaluation.needs_clarification,
        evaluation.should_probe_deeper,
        int(
            (
                perf_counter()
                - started_at
            ) * 1000
        ),
        compact_for_log(
            str(
                evaluation.model_dump()
            )
        )
    )

    return state