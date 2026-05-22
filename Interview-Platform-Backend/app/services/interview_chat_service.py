from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.interview_session import InterviewSession
from app.models.interview_message import InterviewMessage
from app.agents.interview.graph import build_interview_graph


def continue_interview_chat(
    db: Session,
    interview_id: str,
    user_message: str
):

    logger.info(
        "continuing_interview_chat interview_id=%s",
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
            "interview_session_not_found interview_id=%s",
            interview_id
        )

        raise Exception(
            "Interview session not found"
        )

    if interview_session.status == "submitted":
        logger.warning(
            (
                "submitted_interview_chat_rejected "
                "interview_id=%s"
            ),
            interview_id
        )
        raise Exception(
            "Interview has already been submitted"
        )

    existing_messages = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview_id
        )
        .order_by(
            InterviewMessage.created_at.asc()
        )
        .all()
    )

    messages = []

    for message in existing_messages:

        messages.append(
            {
                "role": message.role,
                "content": message.message
            }
        )

    try:

        candidate_message = InterviewMessage(
            interview_id=interview_id,
            role="user",
            message=user_message
        )

        db.add(candidate_message)

        db.commit()

    except Exception:

        db.rollback()

        logger.exception(
            (
                "persist_candidate_message_failed "
                "interview_id=%s"
            ),
            interview_id
        )

        raise

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    logger.info(
        (
            "candidate_message_persisted "
            "interview_id=%s"
        ),
        interview_id
    )

    initial_state = {
        "interview_id": str(
            interview_session.id
        ),

        "system_prompt": (
            interview_session.system_prompt
        ),

        "interview_role": (
            interview_session.role
        ),

        "experience_level": (
            interview_session.experience_level
        ),

        "interview_type": (
            interview_session.interview_type
        ),

        "interview_mode": (
            interview_session.interview_mode
        ),

        "messages": messages,

        "resume_id": (
            str(interview_session.resume_id)
            if interview_session.resume_id
            else None
        ),

        "difficulty": (
            interview_session.difficulty
        ),

        "retrieved_chunks": [],

        "latest_user_message": (
            user_message
        ),

        "current_question": None,

        "question_count": len(
            [
                message
                for message in messages
                if message["role"] == "assistant"
            ]
        )
    }

    graph = build_interview_graph(
        db=db
    )

    config = {
        "configurable": {
            "thread_id": interview_id
        }
    }

    logger.info(
        "invoking_chat_graph interview_id=%s",
        interview_id
    )

    final_state = graph.invoke(
        initial_state,
        config=config
    )

    logger.info(
        (
            "chat_graph_completed "
            "interview_id=%s "
            "question_count=%s"
        ),
        interview_id,
        final_state.get(
            "question_count"
        )
    )

    return {
        "interview_id": interview_id,

        "question": final_state.get(
            "current_question"
        )
    }
