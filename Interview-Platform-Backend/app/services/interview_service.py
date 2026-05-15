from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.interview_session import InterviewSession
from app.schemas.interview_schema import InterviewSetupRequest


DUMMY_USER_ID = "fb341b60-f05b-4cc0-9430-38a7a0b1f524"


def generate_system_prompt(
    interview_data: InterviewSetupRequest
):

    prompt = f"""
    You are conducting a {interview_data.difficulty} difficulty
    {interview_data.interview_type} interview for a
    {interview_data.experience_level} level
    {interview_data.role} candidate.

    Interview mode: {interview_data.interview_mode}

    Conduct the interview professionally.
    Ask one question at a time.
    Evaluate the candidate carefully.
    """

    return prompt.strip()


def create_interview_session(
    db: Session,
    interview_data: InterviewSetupRequest
):

    system_prompt = generate_system_prompt(
        interview_data
    )

    interview_session = InterviewSession(
        user_id=DUMMY_USER_ID,
        role=interview_data.role,
        experience_level=interview_data.experience_level,
        resume_id=interview_data.resume_id,
        difficulty=interview_data.difficulty,
        interview_type=interview_data.interview_type,
        interview_mode=interview_data.interview_mode,
        resume_uploaded=interview_data.resume_uploaded,
        job_description_provided=interview_data.job_description_provided,
        system_prompt=system_prompt
    )

    db.add(interview_session)

    db.commit()

    db.refresh(interview_session)

    logger.info(
        (
            "interview_session_created interview_id=%s "
            "role=%s experience_level=%s difficulty=%s "
            "interview_type=%s interview_mode=%s "
            "resume_uploaded=%s job_description_provided=%s "
            "resume_id=%s"
        ),
        interview_session.id,
        interview_session.role,
        interview_session.experience_level,
        interview_session.difficulty,
        interview_session.interview_type,
        interview_session.interview_mode,
        interview_session.resume_uploaded,
        interview_session.job_description_provided,
        interview_session.resume_id
    )

    return interview_session
