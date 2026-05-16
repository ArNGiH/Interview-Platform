import json
import os
import re
from time import perf_counter

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from app.core.logger import logger

from app.agents.interview.state import (
    InterviewState
)

from app.models.interview_message import (
    InterviewMessage
)

from app.agents.interview.prompts import (
    INTERVIEW_SYSTEM_PROMPT,
    INTERVIEW_INTRO_PROMPT,
    FOLLOWUP_EVALUATION_PROMPT,
    QUESTION_STRATEGY_PROMPT
)

from app.services.llm_service import (
    get_llm
)

from app.services.retrieval_service import (
    retrieve_relevant_resume_chunks
)


llm = get_llm()


LLM_LOG_OUTPUT_CHARS = int(
    os.getenv(
        "LLM_LOG_OUTPUT_CHARS",
        "700"
    )
)


def _compact_for_log(
    text: str | None,
    max_chars: int = LLM_LOG_OUTPUT_CHARS
):

    compact_text = re.sub(
        r"\s+",
        " ",
        text or ""
    ).strip()

    if len(compact_text) > max_chars:
        compact_text = (
            compact_text[:max_chars] + "...[truncated]"
        )

    return json.dumps(
        compact_text
    )


def _usage_metadata(response):

    return getattr(
        response,
        "usage_metadata",
        None
    )


def _parse_strategy_response(
    response_text: str
):

    strategy_match = re.search(
        r"Strategy:\s*([A-Z_]+)",
        response_text or "",
        re.IGNORECASE
    )

    reason_match = re.search(
        r"Reason:\s*(.+)",
        response_text or "",
        re.IGNORECASE | re.DOTALL
    )

    strategy = (
        strategy_match.group(1).upper()
        if strategy_match
        else "UNPARSED"
    )

    reason = (
        reason_match.group(1).strip()
        if reason_match
        else ""
    )

    return strategy, reason


def generate_interview_intro_node(
    state: InterviewState
):

    started_at = perf_counter()

    interview_role = state.get(
        "interview_role",
        "Software Engineer"
    )

    experience_level = state.get(
        "experience_level",
        "mid-level"
    )

    interview_type = state.get(
        "interview_type",
        "technical"
    )

    prompt = f"""
    {INTERVIEW_INTRO_PROMPT}

    Candidate Role:
    {interview_role}

    Experience Level:
    {experience_level}

    Interview Type:
    {interview_type}

    Generate the interview opening message.
    """

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=prompt
                ),
                HumanMessage(
                    content=(
                        "Generate only the interviewer introduction."
                    )
                )
            ]
        )

    except Exception:

        logger.exception(
            "interview_intro_generation_failed"
        )

        raise

    generated_intro = response.content

    state["current_question"] = (
        generated_intro
    )

    state["messages"].append(
        {
            "role": "assistant",
            "content": generated_intro
        }
    )

    state["question_count"] = 1

    logger.info(
        (
            "interview_intro_generated "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "output_preview=%s"
        ),
        len(generated_intro or ""),
        int((perf_counter() - started_at) * 1000),
        _usage_metadata(response),
        _compact_for_log(generated_intro)
    )

    return state



def retrieve_resume_context_node(
    state: InterviewState,
    db
):

    started_at = perf_counter()


    resume_id = state.get(
        "resume_id"
    )

    question_count = state.get(
        "question_count",
        0
    )

    retrieval_query = f"""
    Interview questions for:
    {state.get("latest_user_message", "")}
    """

    try:

        retrieved_chunks = (
            retrieve_relevant_resume_chunks(
                db=db,
                resume_id=resume_id,
                query=retrieval_query,
                top_k=5
            )
        )

    except Exception:

        logger.exception(
            (
                "resume_context_retrieval_failed "
                "resume_id=%s question_count=%s"
            ),
            resume_id,
            question_count
        )

        raise

    state["retrieved_chunks"] = (
        retrieved_chunks
    )

    logger.info(
        (
            "resume_context_retrieved "
            "resume_id=%s question_count=%s "
            "chunks=%s duration_ms=%s"
        ),
        resume_id,
        question_count,
        len(retrieved_chunks),
        int((perf_counter() - started_at) * 1000)
    )

    return state

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

    prompt = f"""
    {FOLLOWUP_EVALUATION_PROMPT}

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
        _usage_metadata(response),
        _compact_for_log(evaluation)
    )

    return state

def generate_interview_question_node(
    state: InterviewState
):

    started_at = perf_counter()

    question_count = state.get(
        "question_count",
        0
    )

    retrieved_context = "\n\n".join(
        state.get(
            "retrieved_chunks",
            []
        )
    )

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

    question_strategy = state.get(
        "question_strategy",
        {}
    )

    strategy_text = (
        question_strategy.get(
            "strategy",
            ""
        )
    )

    prompt = INTERVIEW_SYSTEM_PROMPT.format(
        retrieved_context=retrieved_context,
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        evaluation=evaluation_text,
        strategy=strategy_text,
        question_count=question_count
    )

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=prompt
                ),
                HumanMessage(
                    content=(
                        "Generate the next "
                        "interview question."
                    )
                )
            ]
        )

    except Exception:

        logger.exception(
            (
                "interview_question_generation_failed "
                "question_count=%s "
                "retrieved_chunks=%s"
            ),
            question_count,
            len(
                state.get(
                    "retrieved_chunks",
                    []
                )
            )
        )

        raise

    generated_question = (
        response.content
    )

    state["current_question"] = (
        generated_question
    )

    state["messages"].append(
        {
            "role": "assistant",
            "content": generated_question
        }
    )

    state["question_count"] += 1

    strategy_reason = (
        question_strategy.get(
            "reason",
            ""
        )
    )

    logger.info(
        (
            "interview_question_generated "
            "question_count=%s "
            "strategy=%s "
            "strategy_reason=%s "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "question_preview=%s"
        ),
        state["question_count"],
        strategy_text,
        _compact_for_log(strategy_reason, max_chars=300),
        len(generated_question or ""),
        int((perf_counter() - started_at) * 1000),
        _usage_metadata(response),
        _compact_for_log(generated_question)
    )

    return state


def persist_interview_state_node(
    state: InterviewState,
    db
):

    started_at = perf_counter()


    interview_id = state.get(
        "interview_id"
    )

    messages = state.get(
        "messages",
        []
    )

    if not messages:

        logger.warning(
            (
                "persist_interview_state_skipped "
                "reason=no_messages "
                "interview_id=%s"
            ),
            interview_id
        )

        return state

    latest_message = messages[-1]

    try:

        interview_message = (
            InterviewMessage(
                interview_id=interview_id,
                role=latest_message["role"],
                message=latest_message["content"]
            )
        )

        db.add(interview_message)

        db.commit()

    except Exception:

        db.rollback()

        logger.exception(
            (
                "persist_interview_state_failed "
                "interview_id=%s"
            ),
            interview_id
        )

        raise

    logger.info(
        (
            "interview_message_persisted "
            "interview_id=%s role=%s "
            "duration_ms=%s"
        ),
        interview_id,
        latest_message["role"],
        int((perf_counter() - started_at) * 1000)
    )

    return state

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

    prompt = f"""
    {QUESTION_STRATEGY_PROMPT}

    Previous Question:
    {previous_question}

    Candidate Answer:
    {candidate_answer}

    Evaluation:
    {evaluation_text}
    """

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

    strategy_response = response.content
    strategy, reason = _parse_strategy_response(
        strategy_response
    )

    state["question_strategy"] = {
        "strategy": strategy,
        "reason": reason,
        "raw_response": strategy_response
    }

    logger.info(
        (
            "question_strategy_generated "
            "question_count=%s "
            "strategy=%s "
            "reason=%s "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "output_preview=%s"
        ),
        state.get(
            "question_count",
            0
        ),
        strategy,
        _compact_for_log(reason, max_chars=300),
        len(strategy_response or ""),
        int((perf_counter() - started_at) * 1000),
        _usage_metadata(response),
        _compact_for_log(strategy_response)
    )

    return state
