import json
import re
from time import perf_counter

from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage

from app.core.logger import logger
from app.agents.interview.prompts import FEEDBACK_AGENT_PROMPT
from app.services.llm_service import get_llm


FEEDBACK_AGENT_NAME = "Feedback Agent"


def _extract_json_object(text: str):

    cleaned_text = re.sub(
        r"^```(?:json)?|```$",
        "",
        text.strip(),
        flags=re.MULTILINE
    ).strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        match = re.search(
            r"\{.*\}",
            cleaned_text,
            flags=re.DOTALL
        )

        if match:
            return json.loads(
                match.group(0)
            )

        raise


def _fallback_feedback_report():

    return {
        "overall_summary": (
            "The interview was submitted, but automated feedback "
            "could not be generated reliably."
        ),
        "strengths": [],
        "weaknesses": [
            "Feedback generation failed before a reliable report was produced."
        ],
        "communication_score": 0,
        "technical_score": 0,
        "behavioral_score": 0,
        "confidence_level": "LOW",
        "hiring_recommendation": "LEAN_NO",
        "recommendation_reason": (
            "Insufficient generated feedback is available."
        ),
        "improvement_roadmap": [
            "Retry feedback generation after verifying model availability."
        ],
        "agent_votes": {
            "technical_interviewer": "Not enough reliable feedback generated.",
            "behavioral_interviewer": "Not enough reliable feedback generated.",
            "hiring_manager": "Not enough reliable feedback generated."
        }
    }


def generate_interview_feedback_report(
    interview_session,
    messages
):

    started_at = perf_counter()

    transcript = "\n".join(
        [
            f"{message.role.upper()}: {message.message}"
            for message in messages
        ]
    )

    prompt = f"""
    Interview Context:
    Role: {interview_session.role}
    Experience Level: {interview_session.experience_level}
    Difficulty: {interview_session.difficulty}
    Interview Type: {interview_session.interview_type}
    Interview Mode: {interview_session.interview_mode}

    Transcript:
    {transcript}
    """

    try:
        response = get_llm().invoke(
            [
                SystemMessage(
                    content=FEEDBACK_AGENT_PROMPT
                ),
                HumanMessage(
                    content=prompt
                )
            ]
        )

        report = _extract_json_object(
            response.content
        )

        logger.info(
            (
                "feedback_agent_completed "
                "interview_id=%s "
                "duration_ms=%s "
                "usage=%s"
            ),
            interview_session.id,
            int((perf_counter() - started_at) * 1000),
            getattr(
                response,
                "usage_metadata",
                None
            )
        )

        return report

    except Exception:
        logger.exception(
            (
                "feedback_agent_failed "
                "interview_id=%s"
            ),
            interview_session.id
        )

        return _fallback_feedback_report()
