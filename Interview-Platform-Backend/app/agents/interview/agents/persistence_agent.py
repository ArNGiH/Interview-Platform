from time import perf_counter

from app.core.logger import logger

from app.agents.interview.state import (
    InterviewState
)

from app.models.interview_message import (
    InterviewMessage
)


PERSISTENCE_AGENT_NAME = "Persistence Agent"


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
