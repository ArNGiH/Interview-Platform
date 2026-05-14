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


embedding_model = AzureOpenAIEmbeddings(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
)


def extract_text_from_pdf(
    file
):

    pdf_reader = PdfReader(file)

    extracted_text = ""

    for page in pdf_reader.pages:

        extracted_text += (
            page.extract_text() + "\n"
        )

    return extracted_text


def chunk_resume_text(
    text: str
):

    text_splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50
        )
    )

    chunks = text_splitter.split_text(text)

    return chunks


def generate_embeddings(
    chunks: list[str]
):

    embeddings = (
        embedding_model.embed_documents(chunks)
    )

    return embeddings