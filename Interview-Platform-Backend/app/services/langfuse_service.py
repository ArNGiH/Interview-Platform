from contextlib import contextmanager

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.core.config import (
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
)

langfuse = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST,
)

langfuse_handler = CallbackHandler()


@contextmanager
def agent_observation(
    name: str,
    input_data: dict
):
    with langfuse.start_as_current_observation(
        name=name,
        input=input_data,
    ) as observation:

        try:
            yield observation

        finally:
            langfuse.flush()