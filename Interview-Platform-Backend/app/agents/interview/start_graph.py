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
    generate_interview_intro_node,
    persist_interview_state_node
)


memory = MemorySaver()


def build_start_interview_graph(db):

    graph_builder = StateGraph(
        InterviewState
    )
    graph_builder.add_node(
        "generate_interview_intro",
        generate_interview_intro_node
    )
    graph_builder.add_node(
        "persist_interview_state",
        partial(
            persist_interview_state_node,
            db=db
        )
    )
    graph_builder.set_entry_point(
        "generate_interview_intro"
    )
    graph_builder.add_edge(
        "generate_interview_intro",
        "persist_interview_state"
    )
    graph_builder.add_edge(
        "persist_interview_state",
        END
    )
    return graph_builder.compile(
        checkpointer=memory
    )