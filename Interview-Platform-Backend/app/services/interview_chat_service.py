import json

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.interview_session import InterviewSession
from app.models.interview_message import InterviewMessage
from app.agents.interview.graph import build_interview_graph
from app.agents.interview.agents.interviewer_agent import (
    astream_interviewer_turn
)
from app.agents.interview.agents.common import (
    append_assistant_response
)

from app.agents.interview.agents.persistence_agent import (
    persist_interview_state_node
)


def _stream_token(token: str):
    return f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"


async def continue_interview_chat(
    db: Session,
    interview_id: str,
    user_message: str,
    user_id
):

    logger.info(
        "continuing_interview_chat interview_id=%s",
        interview_id
    )

    interview_session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == interview_id,
            InterviewSession.user_id == user_id
        )
        .first()
    )

    if not interview_session:

        logger.error(
            "interview_session_not_found interview_id=%s",
            interview_id
        )

        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    if interview_session.status == "submitted":
        logger.warning(
            (
                "submitted_interview_chat_rejected "
                "interview_id=%s"
            ),
            interview_id
        )
        raise HTTPException(
            status_code=409,
            detail="Interview has already been submitted"
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
    streaming_prompt = final_state.get(
        "streaming_prompt"
    )

    streaming_instruction = final_state.get(
        "streaming_instruction"
    )

    if not streaming_prompt:

        raise Exception(
            "Streaming prompt missing from graph state"
        )

    full_response = ""

    async for token in astream_interviewer_turn(
        streaming_prompt,
        streaming_instruction
    ):

        full_response += token

        yield _stream_token(token)

    final_state["current_question"] = (
        full_response
    )

    append_assistant_response(
        final_state,
        full_response
    )

    persist_interview_state_node(
        final_state,
        db
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
