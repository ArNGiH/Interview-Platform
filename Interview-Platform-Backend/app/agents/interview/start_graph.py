from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.interview.agents.interviewer_agent import (
    generate_interview_intro_node,
)

from app.agents.interview.state import (
    InterviewState
)


memory = MemorySaver()


def build_start_interview_graph(db):

    graph_builder = StateGraph(
        InterviewState
    )

    graph_builder.add_node(
        "generate_interview_intro",
        generate_interview_intro_node,
    )

    graph_builder.set_entry_point(
        "generate_interview_intro"
    )

    graph_builder.add_edge(
        "generate_interview_intro",
        END,
    )

    return graph_builder.compile(
        checkpointer=memory
    )