from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.core.dependencies import get_db

from app.schemas.interview_schema import (
    InterviewSetupRequest
)
from app.schemas.interview_schema import (
    StartInterviewRequest
)
from app.schemas.interview_schema import (
    InterviewChatRequest
)
from app.services.interview_orchestrator_service import (
    start_interview
)
from app.services.interview_chat_service import (
    continue_interview_chat
)
from app.services.interview_service import (
    create_interview_session,
    get_interview_feedback,
    get_interview_history,
    list_interview_sessions,
    submit_interview_session
)

router = APIRouter(
    prefix="/interview",
    tags=["Interview"]
)


@router.post("/setup")
def setup_interview(
    payload: InterviewSetupRequest,
    db: Session = Depends(get_db)
):

    interview_session = create_interview_session(
        db=db,
        interview_data=payload
    )

    return {
        "interview_id": str(interview_session.id),
        "status": interview_session.status
    }


@router.get("/sessions")
def list_interviews_api(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db)
):

    sessions = list_interview_sessions(
        db=db,
        status=status
    )

    return {
        "sessions": sessions
    }


@router.get("/{interview_id}/history")
def interview_history_api(
    interview_id: str,
    db: Session = Depends(get_db)
):

    return get_interview_history(
        db=db,
        interview_id=interview_id
    )


@router.post("/{interview_id}/submit")
def submit_interview_api(
    interview_id: str,
    db: Session = Depends(get_db)
):

    return submit_interview_session(
        db=db,
        interview_id=interview_id
    )


@router.get("/{interview_id}/feedback")
def interview_feedback_api(
    interview_id: str,
    db: Session = Depends(get_db)
):

    return {
        "feedback": get_interview_feedback(
            db=db,
            interview_id=interview_id
        )
    }

@router.post("/start")
async def start_interview_api(
    payload: StartInterviewRequest,
    db: Session = Depends(get_db)
):
    stream = start_interview(
        db=db,
        interview_id=str(
            payload.interview_id
        )
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream"
    )

@router.post("/chat")
async def interview_chat(
    payload: InterviewChatRequest,
    db: Session = Depends(get_db)
):

    stream = continue_interview_chat(
        db=db,
        interview_id=payload.interview_id,
        user_message=payload.message
    )

    return StreamingResponse(
        stream,
        media_type="text/event-stream"
    )