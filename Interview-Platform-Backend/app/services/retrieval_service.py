from time import perf_counter
from sqlalchemy.orm import Session
from sqlalchemy import select
from pgvector.sqlalchemy import Vector

from app.core.logger import logger
from app.models.resume_chunk import ResumeChunk

from app.services.rag_service import (
    embedding_model
)


def retrieve_relevant_resume_chunks(
    db: Session,
    resume_id: str,
    query: str,
    top_k: int = 5
):

    started_at = perf_counter()

    try:
        query_embedding = (
            embedding_model.embed_query(query)
        )
    except Exception:
        logger.exception(
            (
                "retrieval_query_embedding_failed "
                "resume_id=%s top_k=%s query_chars=%s"
            ),
            resume_id,
            top_k,
            len(query or "")
        )
        raise

    stmt = (
        select(ResumeChunk)
        .where(
            ResumeChunk.resume_id == resume_id
        )
        .order_by(
        ResumeChunk.embedding.cosine_distance(
            query_embedding
        )
    )
        .limit(top_k)
    )

    try:
        results = db.execute(stmt)
    except Exception:
        logger.exception(
            "resume_vector_search_failed resume_id=%s top_k=%s",
            resume_id,
            top_k
        )
        raise

    chunks = results.scalars().all()

    logger.info(
        (
            "resume_vector_search_completed resume_id=%s "
            "top_k=%s chunks=%s duration_ms=%s"
        ),
        resume_id,
        top_k,
        len(chunks),
        int((perf_counter() - started_at) * 1000)
    )

    return [
        chunk.chunk_text
        for chunk in chunks
    ]

def retrieve_full_resume_context(
    db: Session,
    resume_id: str,
    top_k: int = 15
):

    stmt = (
        select(ResumeChunk)
        .where(
            ResumeChunk.resume_id == resume_id
        )
        .order_by(
            ResumeChunk.chunk_order.asc()
        )
        .limit(top_k)
    )

    results = db.execute(stmt)

    chunks = results.scalars().all()

    return [
        chunk.chunk_text
        for chunk in chunks
    ]