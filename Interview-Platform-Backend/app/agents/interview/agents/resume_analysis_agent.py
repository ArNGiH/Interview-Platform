from time import perf_counter

from app.core.logger import logger

from app.agents.interview.state import (
    InterviewState
)

from app.services.retrieval_service import (
    retrieve_relevant_resume_chunks
)


RESUME_ANALYSIS_AGENT_NAME = "Resume Analysis Agent"


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
