import json

from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.interview_session import (
    InterviewSession
)

from app.agents.interview.start_graph import (
    build_start_interview_graph
)

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


async def start_interview(
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

    if interview_session.status == "submitted":

        logger.warning(
            (
                "submitted_interview_start_rejected "
                "interview_id=%s"
            ),
            interview_id
        )

        raise Exception(
            "Interview has already been submitted"
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

        "interview_mode": (
            interview_session.interview_mode
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

        "question_count": 0,

        "streaming_prompt": None,

        "streaming_instruction": None
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
            "interview_graph_completed "
            "interview_id=%s "
            "question_count=%s"
        ),
        interview_id,
        final_state.get(
            "question_count"
        )
    )
