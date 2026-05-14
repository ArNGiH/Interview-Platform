from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db

from app.services.resume_service import (
    upload_resume
)

router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


@router.post("/upload")
def upload_resume_api(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    resume = upload_resume(
        db=db,
        file=file
    )

    return {
        "resume_id": str(resume.id),
        "filename": resume.filename,
        "status": "uploaded"
    }