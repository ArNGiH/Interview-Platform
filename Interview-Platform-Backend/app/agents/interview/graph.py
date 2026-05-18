from functools import partial

from langgraph.graph import (
    StateGraph,
    END
)

from langgraph.checkpoint.memory import (
    MemorySaver
)

from app.agents.interview.state import (
    InterviewState
)

from app.agents.interview.nodes import (
    retrieve_resume_context_node,
    evaluate_candidate_answer_node,
    question_strategy_node,
    persist_interview_state_node,
    clarification_node,
    easier_question_node,
    deep_technical_node,
    topic_transition_node,
    system_design_node,
    conduct_warning_node,
    end_interview_node,
    default_question_node
)


memory = MemorySaver()

def strategy_router(state):

    question_strategy = (
        state.get("question_strategy") or {}
    )
    return question_strategy.get(
        "next_node",
        "default_question_node"
    )

def build_interview_graph(db):

    graph_builder = StateGraph(
        InterviewState
    )

    graph_builder.add_node(
        "retrieve_resume_context",
        partial(
            retrieve_resume_context_node,
            db=db
        )
    )

    graph_builder.add_node(
        "evaluate_candidate_answer",
        evaluate_candidate_answer_node
    )

    graph_builder.add_node(
        "question_strategy",
        question_strategy_node
    )

    graph_builder.add_node(
        "persist_interview_state",
        partial(
            persist_interview_state_node,
            db=db
        )
    )
    graph_builder.add_node(
    "clarification_node",
    clarification_node
)

    graph_builder.add_node(
        "easier_question_node",
        easier_question_node
    )

    graph_builder.add_node(
        "deep_technical_node",
        deep_technical_node
    )

    graph_builder.add_node(
        "topic_transition_node",
        topic_transition_node
    )

    graph_builder.add_node(
        "system_design_node",
        system_design_node
    )

    graph_builder.add_node(
        "conduct_warning_node",
        conduct_warning_node
    )

    graph_builder.add_node(
        "end_interview_node",
        end_interview_node
    )

    graph_builder.add_node(
        "default_question_node",
        default_question_node
    )

    graph_builder.set_entry_point(
        "retrieve_resume_context"
    )

    graph_builder.add_edge(
        "retrieve_resume_context",
        "evaluate_candidate_answer"
    )

    graph_builder.add_edge(
        "evaluate_candidate_answer",
        "question_strategy"
    )

    graph_builder.add_conditional_edges(
    "question_strategy",
    strategy_router,
    {
        "clarification_node":
            "clarification_node",

        "easier_question_node":
            "easier_question_node",

        "deep_technical_node":
            "deep_technical_node",

        "topic_transition_node":
            "topic_transition_node",

        "system_design_node":
            "system_design_node",

        "conduct_warning_node":
            "conduct_warning_node",

        "end_interview_node":
            "end_interview_node",

        "default_question_node":
            "default_question_node"
    }
)

    graph_builder.add_edge(
    "clarification_node",
    "persist_interview_state"
)

    graph_builder.add_edge(
        "easier_question_node",
        "persist_interview_state"
    )

    graph_builder.add_edge(
        "deep_technical_node",
        "persist_interview_state"
    )

    graph_builder.add_edge(
    "topic_transition_node",
    "default_question_node"
)

    graph_builder.add_edge(
        "system_design_node",
        "persist_interview_state"
    )

    graph_builder.add_edge(
        "conduct_warning_node",
        "persist_interview_state"
    )

    graph_builder.add_edge(
        "end_interview_node",
        "persist_interview_state"
    )

    graph_builder.add_edge(
        "default_question_node",
        "persist_interview_state"
    )

    graph_builder.add_edge(
        "persist_interview_state",
        END
    )

    return graph_builder.compile(
        checkpointer=memory
    )