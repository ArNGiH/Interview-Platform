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

from app.services.llm_service import (
    get_llm
)

from app.agents.interview.agents.common import (
    compact_for_log,
    is_behavioral_interview,
    usage_metadata
)


EVALUATION_AGENT_NAME = "Evaluation Agent"

llm = get_llm()


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

    try:

        response = llm.invoke(
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

    except Exception:

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

    evaluation = response.content

    state["candidate_evaluation"] = {
        "question": previous_question,
        "answer": latest_user_message,
        "evaluation": evaluation
    }

    logger.info(
        (
            "candidate_answer_evaluated "
            "question_count=%s "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "evaluation_preview=%s"
        ),
        state.get(
            "question_count",
            0
        ),
        len(evaluation or ""),
        int((perf_counter() - started_at) * 1000),
        usage_metadata(response),
        compact_for_log(evaluation)
    )

    return state
