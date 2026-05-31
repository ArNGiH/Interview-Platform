import inspect

from app.services.langfuse_service import agent_observation

with agent_observation(
    name="test",
    input_data={}
) as observation:

    print(inspect.signature(observation.end))
    print(inspect.signature(observation.update))