from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.core.dependencies import get_db

from app.schemas.interview_schema import (
    InterviewSetupRequest
)

from app.services.interview_service import (
    create_interview_session
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
        "status": "initialized"
    }