from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.interview_session import (
    InterviewSession
)

from app.agents.interview.start_graph import (
    build_start_interview_graph
)


def start_interview(
    db: Session,
    interview_id: str
):

    logger.info(
        "starting_interview interview_id=%s",
        interview_id
    )

    interview_session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == interview_id
        )
        .first()
    )

    if not interview_session:

        logger.error(
            (
                "interview_session_not_found "
                "interview_id=%s"
            ),
            interview_id
        )

        raise Exception(
            "Interview session not found"
        )

    initial_state = {

        "interview_id": str(
            interview_session.id
        ),

        "interview_role": (
        interview_session.role
    ),
         "difficulty": (
            interview_session.difficulty
        ),

        "experience_level": (
            interview_session.experience_level
        ),

        "interview_type": (
            interview_session.interview_type
        ),

        "system_prompt": (
            interview_session.system_prompt
        ),

        "messages": [],

        "resume_id": (
            str(interview_session.resume_id)
            if interview_session.resume_id
            else None
        ),

        "retrieved_chunks": [],

        "latest_user_message": "",

        "current_question": None,

        "question_count": 0
    }

    config = {
        "configurable": {
            "thread_id": str(
                interview_session.id
            )
        }
    }

    logger.info(
        (
            "invoking_interview_graph "
            "interview_id=%s"
        ),
        interview_id
    )

    interview_graph = (
        build_start_interview_graph(
            db=db
        )
    )

    final_state = (
        interview_graph.invoke(
            initial_state,
            config=config
        )
    )

    logger.info(
        (
            "interview_graph_completed "
            "interview_id=%s "
            "question_count=%s"
        ),
        interview_id,
        final_state.get(
            "question_count"
        )
    )

    return {

        "interview_id": str(
            interview_session.id
        ),

        "question": final_state.get(
            "current_question"
        )
    }