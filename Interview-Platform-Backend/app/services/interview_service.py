from sqlalchemy.orm import Session

from app.agents.interview.agents.feedback_agent import (
    generate_interview_feedback_report
)
from app.core.logger import logger
from app.models.interview_feedback import InterviewFeedback
from app.models.interview_message import InterviewMessage
from app.models.interview_session import InterviewSession
from app.schemas.interview_schema import InterviewSetupRequest

DUMMY_USER_ID = "fb341b60-f05b-4cc0-9430-38a7a0b1f524"
INTERVIEW_STATUS_ACTIVE = "active"
INTERVIEW_STATUS_SUBMITTED = "submitted"


def serialize_interview_feedback(
    interview_feedback: InterviewFeedback | None
):

    if not interview_feedback:
        return None

    return {
        "id": str(interview_feedback.id),
        "interview_id": str(interview_feedback.interview_id),
        "report": interview_feedback.report,
        "created_at": (
            interview_feedback.created_at.isoformat()
            if interview_feedback.created_at
            else None
        )
    }

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
    Keep responses short, like a real interviewer.
    Do not reply with long paragraphs.
    Evaluate the candidate carefully.

    If the interview type is behavioral, ask behavioral
    questions only. Do not turn it into a technical screen.

    If the difficulty is easy, start with easy, approachable
    questions and increase only after clear confidence.

    If deeper technical probing is needed, keep it progressive,
    role-relevant, and within normal interview scope.
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
        status=INTERVIEW_STATUS_ACTIVE,
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


def serialize_interview_session(
    db: Session,
    interview_session: InterviewSession
):

    message_count = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview_session.id
        )
        .count()
    )

    latest_message = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview_session.id
        )
        .order_by(
            InterviewMessage.created_at.desc()
        )
        .first()
    )

    return {
        "interview_id": str(interview_session.id),
        "role": interview_session.role,
        "experience_level": interview_session.experience_level,
        "difficulty": interview_session.difficulty,
        "interview_type": interview_session.interview_type,
        "interview_mode": interview_session.interview_mode,
        "status": interview_session.status,
        "resume_uploaded": interview_session.resume_uploaded,
        "job_description_provided": (
            interview_session.job_description_provided
        ),
        "created_at": (
            interview_session.created_at.isoformat()
            if interview_session.created_at
            else None
        ),
        "last_message_at": (
            latest_message.created_at.isoformat()
            if latest_message and latest_message.created_at
            else None
        ),
        "message_count": message_count
    }


def list_interview_sessions(
    db: Session,
    status: str | None = None
):

    query = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.user_id == DUMMY_USER_ID
        )
    )

    if status:
        query = query.filter(
            InterviewSession.status == status.lower()
        )

    interview_sessions = (
        query.order_by(
            InterviewSession.created_at.desc()
        )
        .all()
    )

    logger.info(
        (
            "interview_sessions_listed "
            "status=%s count=%s"
        ),
        status,
        len(interview_sessions)
    )

    return [
        serialize_interview_session(
            db,
            interview_session
        )
        for interview_session in interview_sessions
    ]


def get_interview_history(
    db: Session,
    interview_id: str
):

    interview_session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == interview_id
        )
        .first()
    )

    if not interview_session:
        raise Exception(
            "Interview session not found"
        )

    messages = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview_id
        )
        .order_by(
            InterviewMessage.created_at.asc()
        )
        .all()
    )

    logger.info(
        (
            "interview_history_loaded "
            "interview_id=%s status=%s messages=%s"
        ),
        interview_id,
        interview_session.status,
        len(messages)
    )

    return {
        "session": serialize_interview_session(
            db,
            interview_session
        ),
        "messages": [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.message,
                "created_at": (
                    message.created_at.isoformat()
                    if message.created_at
                    else None
                )
            }
            for message in messages
        ]
    }


def get_interview_feedback(
    db: Session,
    interview_id: str
):

    interview_feedback = (
        db.query(InterviewFeedback)
        .filter(
            InterviewFeedback.interview_id == interview_id
        )
        .first()
    )

    return serialize_interview_feedback(
        interview_feedback
    )


def submit_interview_session(
    db: Session,
    interview_id: str
):

    interview_session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.id == interview_id
        )
        .first()
    )

    if not interview_session:
        raise Exception(
            "Interview session not found"
        )

    messages = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview_id
        )
        .order_by(
            InterviewMessage.created_at.asc()
        )
        .all()
    )

    report = generate_interview_feedback_report(
        interview_session,
        messages
    )

    interview_feedback = (
        db.query(InterviewFeedback)
        .filter(
            InterviewFeedback.interview_id == interview_id
        )
        .first()
    )

    if interview_feedback:
        interview_feedback.report = report
    else:
        interview_feedback = InterviewFeedback(
            interview_id=interview_id,
            report=report
        )
        db.add(interview_feedback)

    interview_session.status = INTERVIEW_STATUS_SUBMITTED

    db.commit()

    db.refresh(interview_session)
    db.refresh(interview_feedback)

    logger.info(
        (
            "interview_session_submitted "
            "interview_id=%s"
        ),
        interview_id
    )

    return {
        "session": serialize_interview_session(
            db,
            interview_session
        ),
        "feedback": serialize_interview_feedback(
            interview_feedback
        )
    }
