from time import perf_counter
import asyncio

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)
from app.services.langfuse_service import (
    agent_observation
)

from app.core.logger import logger

from app.agents.interview.prompts import (
    INTERVIEW_SYSTEM_PROMPT,
    INTERVIEW_INTRO_PROMPT,
    CLARIFICATION_PROMPT,
    EASY_RECOVERY_PROMPT,
    DEEP_TECHNICAL_PROMPT,
    END_INTERVIEW_PROMPT,
    CONDUCT_WARNING_PROMPT,
    SYSTEM_DESIGN_PROMPT,
    DEFAULT_QUESTION_PROMPT,
    BEHAVIORAL_QUESTION_PROMPT
)

from app.agents.interview.state import (
    InterviewState
)


from app.services.llm_service import (
    get_llm
)

from app.agents.interview.agents.common import (
    append_assistant_response,
    compact_for_log,
    fallback_behavioral_question,
    is_behavioral_interview,
    log_agent_output,
    model_dump_for_prompt,
    state_upper,
    structured_get,
    usage_metadata
)


INTERVIEWER_AGENT_NAME = "Interviewer Agent"

llm = get_llm()

async def astream_interviewer_turn(
    prompt: str,
    instruction: str
):

    with agent_observation(
        name="Interviewer Response Generation",
        input_data={
            "instruction": instruction,
            "prompt_chars": len(prompt)
        }
    ) as observation:

        full_response = ""

        try:

            async for chunk in llm.astream(
                [
                    SystemMessage(
                        content=prompt
                    ),
                    HumanMessage(
                        content=instruction
                    )
                ]
            ):

                if chunk.content:

                    full_response += (
                        chunk.content
                    )

                    yield chunk.content

                    await asyncio.sleep(0)

            observation.update(
                output={
                    "response_length": len(
                        full_response
                    )
                }
            )
            observation.end()

        except Exception:

            raise

def generate_interview_intro_node(
    state: InterviewState
):

    started_at = perf_counter()

    interview_role = state.get(
        "interview_role",
        "Software Engineer"
    )

    experience_level = state.get(
        "experience_level",
        "mid-level"
    )

    interview_type = state.get(
        "interview_type",
        "technical"
    )

    prompt = f"""
    {INTERVIEW_INTRO_PROMPT}

    Candidate Role:
    {interview_role}

    Experience Level:
    {experience_level}

    Interview Type:
    {interview_type}

    Generate the interview opening message.
    """

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate only the interviewer introduction."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=generate_interview_intro "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state

def generate_interview_question_node(
    state: InterviewState
):

    started_at = perf_counter()

    question_count = state.get(
        "question_count",
        0
    )

    retrieved_context = "\n\n".join(
        state.get(
            "retrieved_chunks",
            []
        )
    )

    candidate_evaluation = state.get(
        "candidate_evaluation",
    )

    evaluation_text = (
        structured_get(candidate_evaluation, "summary", "")
    )

    previous_question = (
        structured_get(candidate_evaluation, "question", "")
    )

    candidate_answer = (
        structured_get(candidate_evaluation, "answer", "")
    )

    question_strategy = state.get(
        "question_strategy"
    )

    strategy_text = (
        structured_get(question_strategy, "strategy_type", "")
    )

    prompt = INTERVIEW_SYSTEM_PROMPT.format(
        retrieved_context=retrieved_context,
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        evaluation=evaluation_text,
        strategy=strategy_text,
        difficulty=state.get(
            "difficulty",
            "MEDIUM"
        ),
        interview_role=state.get(
            "interview_role",
            "Software Engineer"
        ),
        experience_level=state.get(
            "experience_level",
            "mid-level"
        ),
        interview_type=state.get(
            "interview_type",
            "technical"
        ),
        question_count=question_count
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate the next interview question."
    )

    strategy_reason = (
        structured_get(
            question_strategy,
            "reasoning",
            ""
        )
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=generate_interview_question "
            "question_count=%s "
            "strategy=%s "
            "strategy_reason=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        question_count,
        strategy_text,
        compact_for_log(strategy_reason),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state

def clarification_node(state):

    started_at = perf_counter()

    logger.info(
        "clarification_node_started"
    )

    previous_question = (
        state["messages"][-2]["content"]
        if len(state["messages"]) >= 2
        else ""
    )

    candidate_answer = (
        state.get(
            "latest_user_message",
            ""
        )
    )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    prompt = CLARIFICATION_PROMPT.format(
        current_topic=state.get(
            "current_topic"
        ),
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate the clarification turn."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=clarification_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state


def easier_question_node(state):

    started_at = perf_counter()

    logger.info(
        "easier_question_node_started"
    )

    if is_behavioral_interview(state):

        logger.info(
            (
                "easier_question_redirected "
                "reason=behavioral_interview "
                "target_node=default_question_node"
            )
        )

        return default_question_node(
            state
        )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    evaluation = (
        state.get(
            "candidate_evaluation"
        )
    )

    prompt = EASY_RECOVERY_PROMPT.format(
        current_topic=state.get(
            "current_topic"
        ),
        interview_role=state.get(
            "interview_role"
        ),
        interview_type=state_upper(
            state,
            "interview_type",
            "technical"
        ),
        requested_difficulty=state_upper(
            state,
            "difficulty",
            "medium"
        ),
        evaluation=model_dump_for_prompt(
            evaluation
        ),
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate an easier recovery question."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=easier_question_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state

def deep_technical_node(state):

    started_at = perf_counter()

    logger.info(
        "deep_technical_node_started"
    )

    previous_question = (
        state["messages"][-2]["content"]
        if len(state["messages"]) >= 2
        else ""
    )

    candidate_answer = (
        state.get(
            "latest_user_message",
            ""
        )
    )

    evaluation = (
        state.get(
            "candidate_evaluation"
        )
    )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    prompt = DEEP_TECHNICAL_PROMPT.format(
        interview_role=state.get(
            "interview_role"
        ),
        experience_level=state.get(
            "experience_level"
        ),
        requested_difficulty=state_upper(
            state,
            "difficulty",
            "medium"
        ),
        question_count=state.get(
            "question_count",
            0
        ),
        current_topic=state.get(
            "current_topic"
        ),
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        evaluation=model_dump_for_prompt(
            evaluation
        ),
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate a progressive technical follow-up question."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=deep_technical_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state


def topic_transition_node(state):

    started_at = perf_counter()

    logger.info(
        "topic_transition_node_started"
    )

    next_topic = (
        structured_get(
            state.get("question_strategy"),
            "next_topic"
        )
    )

    if next_topic:

        state["current_topic"] = (
            next_topic
        )

        topic_history = (
            state.get(
                "topic_history",
                []
            )
        )

        topic_history.append(
            next_topic
        )

        state["topic_history"] = (
            topic_history
        )

    logger.info(
        (
            "interview_node_output "
            "node=topic_transition_node "
            "interview_id=%s "
            "next_topic=%s "
            "topic_history=%s "
            "duration_ms=%s"
        ),
        state.get(
            "interview_id"
        ),
        next_topic,
        state.get(
            "topic_history",
            []
        ),
        int((perf_counter() - started_at) * 1000)
    )

    if is_behavioral_interview(state):

        return default_question_node(
            state
        )

    return generate_interview_question_node(
        state
    )

def system_design_node(state):

    started_at = perf_counter()

    logger.info(
        "system_design_node_started"
    )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    evaluation = (
        state.get(
            "candidate_evaluation"
        )
    )

    prompt = SYSTEM_DESIGN_PROMPT.format(
        interview_role=state.get(
            "interview_role"
        ),
        experience_level=state.get(
            "experience_level"
        ),
        requested_difficulty=state_upper(
            state,
            "difficulty",
            "medium"
        ),
        interview_type=state_upper(
            state,
            "interview_type",
            "technical"
        ),
        current_topic=state.get(
            "current_topic"
        ),
        evaluation=model_dump_for_prompt(
            evaluation
        ),
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate one system design interview question."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=system_design_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state


def conduct_warning_node(state):

    started_at = perf_counter()

    logger.info(
        "conduct_warning_node_started"
    )

    previous_question = (
        state["messages"][-2]["content"]
        if len(state["messages"]) >= 2
        else ""
    )

    candidate_answer = (
        state.get(
            "latest_user_message",
            ""
        )
    )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    prompt = CONDUCT_WARNING_PROMPT.format(
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate the conduct warning."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=conduct_warning_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state
def end_interview_node(state):

    started_at = perf_counter()

    logger.info(
        "end_interview_node_started"
    )

    candidate_answer = (
        state.get(
            "latest_user_message",
            ""
        )
    )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    prompt = END_INTERVIEW_PROMPT.format(
        candidate_answer=candidate_answer,
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate the closing interviewer message."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=end_interview_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state


def default_question_node(state):

    started_at = perf_counter()

    logger.info(
        "default_question_node_started"
    )

    previous_question = (
        state["messages"][-2]["content"]
        if len(state["messages"]) >= 2
        else ""
    )

    candidate_answer = (
        state.get(
            "latest_user_message",
            ""
        )
    )

    evaluation = (
        state.get(
            "candidate_evaluation"
        )
    )

    question_strategy = (
        state.get(
            "question_strategy"
        )
    )

    prompt_template = (
        BEHAVIORAL_QUESTION_PROMPT
        if is_behavioral_interview(state)
        else DEFAULT_QUESTION_PROMPT
    )

    prompt = prompt_template.format(
        interview_role=state.get(
            "interview_role"
        ),
        experience_level=state.get(
            "experience_level"
        ),
        interview_type=state_upper(
            state,
            "interview_type",
            "technical"
        ),
        requested_difficulty=state_upper(
            state,
            "difficulty",
            "medium"
        ),
        question_count=state.get(
            "question_count",
            0
        ),
        current_topic=state.get(
            "current_topic"
        ),
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        evaluation=model_dump_for_prompt(
            evaluation
        ),
        reasoning=structured_get(
            question_strategy,
            "reasoning"
        )
    )

    state["streaming_prompt"] = prompt

    state["streaming_instruction"] = (
        "Generate the next interviewer question."
    )

    logger.info(
        (
            "streaming_payload_prepared "
            "node=default_question_node "
            "interview_id=%s "
            "duration_ms=%s "
            "prompt_chars=%s"
        ),
        state.get(
            "interview_id"
        ),
        int((perf_counter() - started_at) * 1000),
        len(prompt or "")
    )

    return state


INTERVIEWER_AGENT_NODES = {
    "intro": generate_interview_intro_node,
    "default_question": default_question_node,
    "deep_technical": deep_technical_node,
    "easier_question": easier_question_node,
    "clarification": clarification_node,
    "topic_transition": topic_transition_node,
    "system_design": system_design_node,
    "conduct_warning": conduct_warning_node,
    "end_interview": end_interview_node,
    "general_question": generate_interview_question_node
}
