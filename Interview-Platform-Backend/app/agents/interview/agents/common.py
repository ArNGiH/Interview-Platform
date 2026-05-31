import json
import os
import re
from time import perf_counter

from pydantic import BaseModel

from app.agents.interview.state import InterviewState
from app.core.logger import logger

LLM_LOG_OUTPUT_CHARS = int(os.getenv("LLM_LOG_OUTPUT_CHARS", "0"))


def compact_for_log(text: str | None, max_chars: int = LLM_LOG_OUTPUT_CHARS):
    compact_text = re.sub(r"\s+", " ", text or "").strip()

    if max_chars > 0 and len(compact_text) > max_chars:
        compact_text = compact_text[:max_chars] + "...[truncated]"

    return json.dumps(compact_text)


def model_dump_for_prompt(value):
    if isinstance(value, BaseModel):
        return value.model_dump()

    return value or {}


def normalize_structured_output(response, schema):
    if isinstance(response, schema):
        return response

    parsed = getattr(response, "parsed", None)

    if isinstance(parsed, schema):
        return parsed

    if isinstance(response, dict):
        parsed = response.get("parsed")

        if isinstance(parsed, schema):
            return parsed

        return schema.model_validate(response)

    field_values = {}

    for field_name in schema.model_fields:
        if hasattr(response, field_name):
            field_values[field_name] = getattr(response, field_name)

    if field_values:
        return schema.model_validate(field_values)

    return schema.model_validate(response)


def structured_get(value, key: str, default=None):
    if isinstance(value, BaseModel):
        return getattr(value, key, default)

    if isinstance(value, dict):
        return value.get(key, default)

    return default


def usage_metadata(response):
    return getattr(response, "usage_metadata", None)


def state_upper(state: InterviewState, key: str, default: str):
    return (state.get(key, default) or default).upper()


def is_behavioral_interview(state: InterviewState):
    return (state.get("interview_type", "") or "").lower() == "behavioral"


def fallback_behavioral_question():
    return (
        "What was the reason behind that decision, "
        "and what did you learn from it?"
    )


def append_assistant_response(state: InterviewState, content: str | None):
    state["current_question"] = content
    state["messages"].append(
        {
            "role": "assistant",
            "content": content,
        }
    )
    state["question_count"] = state.get("question_count", 0) + 1


def log_agent_output(
    agent_name: str,
    node_name: str,
    state: InterviewState,
    response,
    started_at: float,
    output_override: str | None = None,
):
    content = (
        output_override
        if output_override is not None
        else getattr(
            response,
            "content",
            getattr(response, "message", response)
        )
    )

    content = str(content or "")

    logger.info(
        (
            "interview_agent_output "
            "agent=%s node=%s "
            "interview_id=%s "
            "question_count=%s "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "output=%s"
        ),
        agent_name,
        node_name,
        state.get("interview_id"),
        state.get("question_count", 0),
        len(content or ""),
        int((perf_counter() - started_at) * 1000),
        usage_metadata(response),
        compact_for_log(content),
    )


