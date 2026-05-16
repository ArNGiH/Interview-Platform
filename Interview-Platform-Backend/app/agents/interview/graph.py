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
    generate_interview_question_node,
    persist_interview_state_node
)


memory = MemorySaver()


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
        "generate_interview_question",
        generate_interview_question_node
    )

    graph_builder.add_node(
        "persist_interview_state",
        partial(
            persist_interview_state_node,
            db=db
        )
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

    graph_builder.add_edge(
        "question_strategy",
        "generate_interview_question"
    )

    graph_builder.add_edge(
        "generate_interview_question",
        "persist_interview_state"
    )

    graph_builder.add_edge(
        "persist_interview_state",
        END
    )

    return graph_builder.compile(
        checkpointer=memory
    )