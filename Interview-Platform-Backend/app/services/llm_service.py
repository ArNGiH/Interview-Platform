from urllib.parse import urlparse

from langchain_openai import AzureChatOpenAI

from app.core.logger import logger
from app.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


def get_llm():

    endpoint_host = urlparse(
        AZURE_OPENAI_ENDPOINT or ""
    ).netloc

    logger.info(
        (
            "llm_client_init provider=azure_openai "
            "deployment=%s api_version=%s endpoint_host=%s"
        ),
        AZURE_OPENAI_DEPLOYMENT,
        AZURE_OPENAI_API_VERSION,
        endpoint_host
    )

    return AzureChatOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        api_version=AZURE_OPENAI_API_VERSION,
        streaming=True,
    )