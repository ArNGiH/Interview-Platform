from functools import partial

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.interview.agents.evaluation_agent import (
    evaluate_candidate_answer_node,
)
from app.agents.interview.agents.interviewer_agent import (
    clarification_node,
    conduct_warning_node,
    deep_technical_node,
    default_question_node,
    easier_question_node,
    end_interview_node,
    system_design_node,
    topic_transition_node,
)
from app.agents.interview.agents.orchestrator_agent import (
    question_strategy_node,
)
from app.agents.interview.agents.persistence_agent import (
    persist_interview_state_node,
)
from app.agents.interview.agents.resume_analysis_agent import (
    retrieve_resume_context_node,
)
from app.agents.interview.state import InterviewState
from app.core.logger import logger


memory = MemorySaver()


def strategy_router(state):
    question_strategy = state.get("question_strategy") or {}
    requested_node = question_strategy.get(
        "next_node",
        "default_question_node",
    )

    interview_type = (state.get("interview_type", "") or "").lower()
    difficulty = (state.get("difficulty", "") or "").lower()
    question_count = state.get("question_count", 0)

    if (
        interview_type == "behavioral"
        and requested_node in {"deep_technical_node", "system_design_node"}
    ):
        logger.info(
            (
                "strategy_route_overridden "
                "reason=behavioral_interview "
                "requested_node=%s fallback_node=default_question_node"
            ),
            requested_node,
        )
        return "default_question_node"

    if (
        difficulty == "easy"
        and question_count <= 2
        and requested_node in {"deep_technical_node", "system_design_node"}
    ):
        logger.info(
            (
                "strategy_route_overridden "
                "reason=easy_interview_early_stage "
                "question_count=%s requested_node=%s "
                "fallback_node=default_question_node"
            ),
            question_count,
            requested_node,
        )
        return "default_question_node"

    return requested_node


def build_interview_graph(db):
    graph_builder = StateGraph(InterviewState)

    graph_builder.add_node(
        "retrieve_resume_context",
        partial(retrieve_resume_context_node, db=db),
    )
    graph_builder.add_node(
        "evaluate_candidate_answer",
        evaluate_candidate_answer_node,
    )
    graph_builder.add_node(
        "question_strategy",
        question_strategy_node,
    )
    graph_builder.add_node(
        "persist_interview_state",
        partial(persist_interview_state_node, db=db),
    )
    graph_builder.add_node(
        "clarification_node",
        clarification_node,
    )
    graph_builder.add_node(
        "easier_question_node",
        easier_question_node,
    )
    graph_builder.add_node(
        "deep_technical_node",
        deep_technical_node,
    )
    graph_builder.add_node(
        "topic_transition_node",
        topic_transition_node,
    )
    graph_builder.add_node(
        "system_design_node",
        system_design_node,
    )
    graph_builder.add_node(
        "conduct_warning_node",
        conduct_warning_node,
    )
    graph_builder.add_node(
        "end_interview_node",
        end_interview_node,
    )
    graph_builder.add_node(
        "default_question_node",
        default_question_node,
    )

    graph_builder.set_entry_point("retrieve_resume_context")
    graph_builder.add_edge(
        "retrieve_resume_context",
        "evaluate_candidate_answer",
    )
    graph_builder.add_edge(
        "evaluate_candidate_answer",
        "question_strategy",
    )

    graph_builder.add_conditional_edges(
        "question_strategy",
        strategy_router,
        {
            "clarification_node": "clarification_node",
            "easier_question_node": "easier_question_node",
            "deep_technical_node": "deep_technical_node",
            "topic_transition_node": "topic_transition_node",
            "system_design_node": "system_design_node",
            "conduct_warning_node": "conduct_warning_node",
            "end_interview_node": "end_interview_node",
            "default_question_node": "default_question_node",
        },
    )

    for node_name in (
        "clarification_node",
        "easier_question_node",
        "deep_technical_node",
        "topic_transition_node",
        "system_design_node",
        "conduct_warning_node",
        "end_interview_node",
        "default_question_node",
    ):
        graph_builder.add_edge(
            node_name,
            "persist_interview_state",
        )

    graph_builder.add_edge("persist_interview_state", END)

    return graph_builder.compile(checkpointer=memory)
