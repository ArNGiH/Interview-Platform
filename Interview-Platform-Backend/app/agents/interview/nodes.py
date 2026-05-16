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
    INTERVIEW_INTRO_PROMPT
)

from app.services.llm_service import (
    get_llm
)

from app.services.retrieval_service import (
    retrieve_relevant_resume_chunks
)


llm = get_llm()

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
            "duration_ms=%s"
        ),
        len(generated_intro or ""),
        int((perf_counter() - started_at) * 1000)
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


def generate_interview_question_node(
    state: InterviewState
):

    started_at = perf_counter()

    question_count = state.get(
        "question_count",
        0
    )

    retrieved_context = "\n\n".join(
        state.get("retrieved_chunks", [])
    )

    conversation_history = "\n".join(
        [
            (
                f"{message['role']}: "
                f"{message['content']}"
            )
            for message in state.get(
                "messages",
                []
            )
        ]
    )

    prompt = f"""
    {INTERVIEW_SYSTEM_PROMPT}

    Resume Context:
    {retrieved_context}

    Conversation History:
    {conversation_history}

    Current Question Count:
    {question_count}

    Generate the next interview question.

    Rules:
    - Ask only one question
    - Make it realistic
    - Use resume context when relevant
    - Avoid repeating previous questions
    - Keep interviewer tone professional
    """

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
                "history_messages=%s "
                "retrieved_chunks=%s"
            ),
            question_count,
            len(state.get("messages", [])),
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

    usage = getattr(
        response,
        "usage_metadata",
        None
    )

    logger.info(
        (
            "interview_question_generated "
            "question_count=%s "
            "history_messages=%s "
            "retrieved_chunks=%s "
            "response_chars=%s "
            "duration_ms=%s usage=%s"
        ),
        state["question_count"],
        len(state.get("messages", [])),
        len(state.get("retrieved_chunks", [])),
        len(generated_question or ""),
        int((perf_counter() - started_at) * 1000),
        usage
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