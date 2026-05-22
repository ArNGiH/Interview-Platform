from time import perf_counter

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
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
    has_behavioral_technical_leak,
    is_behavioral_interview,
    log_agent_output,
    state_upper,
    usage_metadata
)


INTERVIEWER_AGENT_NAME = "Interviewer Agent"

llm = get_llm()


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

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=prompt
                ),
                HumanMessage(
                    content=(
                        "Generate only the interviewer introduction."
                    )
                )
            ]
        )

    except Exception:

        logger.exception(
            "interview_intro_generation_failed"
        )

        raise

    generated_intro = response.content

    append_assistant_response(
        state,
        generated_intro
    )

    logger.info(
        (
            "interview_node_output "
            "node=generate_interview_intro "
            "interview_id=%s "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "output=%s"
        ),
        state.get(
            "interview_id"
        ),
        len(generated_intro or ""),
        int((perf_counter() - started_at) * 1000),
        usage_metadata(response),
        compact_for_log(generated_intro)
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
        {}
    )

    evaluation_text = (
        candidate_evaluation.get(
            "evaluation",
            ""
        )
    )

    previous_question = (
        candidate_evaluation.get(
            "question",
            ""
        )
    )

    candidate_answer = (
        candidate_evaluation.get(
            "answer",
            ""
        )
    )

    question_strategy = state.get(
        "question_strategy",
        {}
    )

    strategy_text = (
        question_strategy.get(
            "strategy_type",
            ""
        )
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

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=prompt
                ),
                HumanMessage(
                    content=(
                        "Generate the next "
                        "interview question."
                    )
                )
            ]
        )

    except Exception:

        logger.exception(
            (
                "interview_question_generation_failed "
                "question_count=%s "
                "retrieved_chunks=%s"
            ),
            question_count,
            len(
                state.get(
                    "retrieved_chunks",
                    []
                )
            )
        )

        raise

    generated_question = (
        response.content
    )

    append_assistant_response(
        state,
        generated_question
    )

    strategy_reason = (
        question_strategy.get(
            "reasoning",
            ""
        )
    )

    logger.info(
        (
            "interview_node_output "
            "node=generate_interview_question "
            "question_count=%s "
            "strategy=%s "
            "strategy_reason=%s "
            "response_chars=%s "
            "duration_ms=%s "
            "usage=%s "
            "output=%s"
        ),
        state["question_count"],
        strategy_text,
        compact_for_log(strategy_reason, max_chars=300),
        len(generated_question or ""),
        int((perf_counter() - started_at) * 1000),
        usage_metadata(response),
        compact_for_log(generated_question)
    )

    return state

def clarification_node(state):

    started_at = perf_counter()

    logger.info(
        "clarification_node_started"
    )

    llm = get_llm()

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
            "question_strategy",
            {}
        )
    )

    prompt = CLARIFICATION_PROMPT.format(
        current_topic=state.get(
            "current_topic"
        ),
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)
    append_assistant_response(
        state,
        response.content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "clarification_node",
        state,
        response,
        started_at
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

    llm = get_llm()

    question_strategy = (
        state.get(
            "question_strategy",
            {}
        )
    )

    evaluation = (
        state.get(
            "candidate_evaluation",
            {}
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
        evaluation=evaluation,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)
    append_assistant_response(
        state,
        response.content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "easier_question_node",
        state,
        response,
        started_at
    )
    return state

def deep_technical_node(state):

    started_at = perf_counter()

    logger.info(
        "deep_technical_node_started"
    )
    llm = get_llm()
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
            "candidate_evaluation",
            {}
        )
    )
    question_strategy = (
        state.get(
            "question_strategy",
            {}
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
        evaluation=evaluation,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)
    append_assistant_response(
        state,
        response.content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "deep_technical_node",
        state,
        response,
        started_at
    )

    return state

def topic_transition_node(state):

    started_at = perf_counter()

    logger.info(
        "topic_transition_node_started"
    )
    next_topic = (
        state.get(
            "question_strategy",
            {}
        ).get(
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

    llm = get_llm()

    question_strategy = (
        state.get(
            "question_strategy",
            {}
        )
    )

    evaluation = (
        state.get(
            "candidate_evaluation",
            {}
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
        evaluation=evaluation,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)
    append_assistant_response(
        state,
        response.content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "system_design_node",
        state,
        response,
        started_at
    )
    return state

def conduct_warning_node(state):

    started_at = perf_counter()

    logger.info(
        "conduct_warning_node_started"
    )

    llm = get_llm()

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
            "question_strategy",
            {}
        )
    )
    prompt = CONDUCT_WARNING_PROMPT.format(
        previous_question=previous_question,
        candidate_answer=candidate_answer,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)
    append_assistant_response(
        state,
        response.content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "conduct_warning_node",
        state,
        response,
        started_at
    )

    return state

def end_interview_node(state):

    started_at = perf_counter()

    logger.info(
        "end_interview_node_started"
    )
    llm = get_llm()
    candidate_answer = (
        state.get(
            "latest_user_message",
            ""
        )
    )
    question_strategy = (
        state.get(
            "question_strategy",
            {}
        )
    )
    prompt = END_INTERVIEW_PROMPT.format(
        candidate_answer=candidate_answer,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)
    append_assistant_response(
        state,
        response.content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "end_interview_node",
        state,
        response,
        started_at
    )

    return state

def default_question_node(state):

    started_at = perf_counter()

    logger.info(
        "default_question_node_started"
    )

    llm = get_llm()

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
            "candidate_evaluation",
            {}
        )
    )

    question_strategy = (
        state.get(
            "question_strategy",
            {}
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
        evaluation=evaluation,
        reasoning=question_strategy.get(
            "reasoning"
        )
    )
    response = llm.invoke(prompt)

    response_content = response.content

    if (
        is_behavioral_interview(state)
        and has_behavioral_technical_leak(response_content)
    ):
        logger.warning(
            (
                "behavioral_question_rewritten "
                "reason=technical_language_detected "
                "interview_id=%s original_output=%s"
            ),
            state.get(
                "interview_id"
            ),
            compact_for_log(response_content)
        )
        response_content = fallback_behavioral_question()

    append_assistant_response(
        state,
        response_content
    )
    log_agent_output(
        INTERVIEWER_AGENT_NAME,
        "default_question_node",
        state,
        response,
        started_at,
        output_override=response_content
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
