from time import perf_counter

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from app.core.logger import logger

from app.agents.interview.state import (
    InterviewState
)

from app.agents.interview.prompts import (
    RESUME_ANALYSIS_PROMPT
)

from app.agents.interview.schemas import (
    ResumeAnalysisOutput
)

from app.services.llm_service import (
    get_llm
)

from app.services.retrieval_service import (
    retrieve_full_resume_context
)

from app.services.langfuse_service import (
    agent_observation
)
from app.agents.interview.agents.common import (
    compact_for_log,
    normalize_structured_output
)


RESUME_ANALYSIS_AGENT_NAME = (
    "Resume Analysis Agent"
)

llm = get_llm()

structured_llm = llm.with_structured_output(
    ResumeAnalysisOutput
)


def analyze_resume_node(
    state: InterviewState,
    db
):

    started_at = perf_counter()

    resume_id = state.get(
        "resume_id"
    )

    with agent_observation(
        name="Resume Analysis",
        input_data={
            "resume_id": resume_id,
            "interview_id": state.get(
                "interview_id"
            )
        }
    ) as observation:

        try:

            retrieved_chunks = (
                retrieve_full_resume_context(
                    db=db,
                    resume_id=resume_id
                )
            )

            resume_context = "\n\n".join(
                retrieved_chunks
            )

            prompt = f"""
            Candidate Resume Context:

            {resume_context}

            Analyze this candidate resume.
            """

            raw_response = structured_llm.invoke(
                [
                    SystemMessage(
                        content=RESUME_ANALYSIS_PROMPT
                    ),
                    HumanMessage(
                        content=prompt
                    )
                ]
            )

            response = normalize_structured_output(
                raw_response,
                ResumeAnalysisOutput
            )

            observation.update(
                output={
                    "retrieved_chunk_count": len(
                        retrieved_chunks
                    ),
                    "analysis": response.model_dump()
                }
            )
            observation.end()

        except Exception as ex:


            logger.exception(
                "resume_analysis_failed"
            )

            raise

    state["resume_analysis"] = response

    logger.info(
        (
            "resume_analysis_completed "
            "interview_id=%s "
            "duration_ms=%s "
            "analysis=%s"
        ),
        state.get(
            "interview_id"
        ),
        int(
            (
                perf_counter()
                - started_at
            ) * 1000
        ),
        compact_for_log(
            str(
                response.model_dump()
            )
        )
    )

    return state