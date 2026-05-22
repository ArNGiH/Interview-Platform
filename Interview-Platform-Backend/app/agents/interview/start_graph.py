from functools import partial

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.interview.agents.interviewer_agent import (
    generate_interview_intro_node,
)
from app.agents.interview.agents.persistence_agent import (
    persist_interview_state_node,
)
from app.agents.interview.state import InterviewState


memory = MemorySaver()


def build_start_interview_graph(db):
    graph_builder = StateGraph(InterviewState)

    graph_builder.add_node(
        "generate_interview_intro",
        generate_interview_intro_node,
    )
    graph_builder.add_node(
        "persist_interview_state",
        partial(persist_interview_state_node, db=db),
    )

    graph_builder.set_entry_point("generate_interview_intro")
    graph_builder.add_edge(
        "generate_interview_intro",
        "persist_interview_state",
    )
    graph_builder.add_edge("persist_interview_state", END)

    return graph_builder.compile(checkpointer=memory)
