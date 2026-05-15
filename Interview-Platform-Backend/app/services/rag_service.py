from time import perf_counter

from pypdf import PdfReader

from langchain_openai import (
    AzureOpenAIEmbeddings
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from app.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT
)
from app.core.logger import logger


embedding_model = AzureOpenAIEmbeddings(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
)


def extract_text_from_pdf(
    file
):

    started_at = perf_counter()
    pdf_reader = PdfReader(file)

    extracted_text = ""

    empty_pages = 0

    for page in pdf_reader.pages:

        page_text = page.extract_text()

        if not page_text:
            empty_pages += 1
            continue

        extracted_text += (
            page_text + "\n"
        )

    logger.info(
        (
            "pdf_text_extracted pages=%s chars=%s "
            "empty_pages=%s duration_ms=%s"
        ),
        len(pdf_reader.pages),
        len(extracted_text),
        empty_pages,
        int((perf_counter() - started_at) * 1000)
    )

    if not extracted_text.strip():
        logger.warning(
            "pdf_text_empty pages=%s",
            len(pdf_reader.pages)
        )

    return extracted_text


def chunk_resume_text(
    text: str
):

    started_at = perf_counter()
    text_splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50
        )
    )

    chunks = text_splitter.split_text(text)

    logger.info(
        (
            "resume_text_chunked input_chars=%s chunks=%s "
            "duration_ms=%s"
        ),
        len(text or ""),
        len(chunks),
        int((perf_counter() - started_at) * 1000)
    )

    return chunks


def generate_embeddings(
    chunks: list[str]
):

    started_at = perf_counter()

    try:
        embeddings = (
            embedding_model.embed_documents(chunks)
        )
    except Exception:
        logger.exception(
            (
                "resume_embedding_generation_failed "
                "chunks=%s total_chars=%s"
            ),
            len(chunks),
            sum(len(chunk) for chunk in chunks)
        )
        raise

    logger.info(
        (
            "resume_embeddings_generated deployment=%s "
            "chunks=%s vectors=%s duration_ms=%s"
        ),
        AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        len(chunks),
        len(embeddings),
        int((perf_counter() - started_at) * 1000)
    )

    return embeddings
