import io
import uuid
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.resume import Resume
from app.models.resume_chunk import ResumeChunk
from app.services.storage.s3_service import (
    upload_file_to_s3
)
from app.services.rag_service import (
    extract_text_from_pdf,
    chunk_resume_text,
    generate_embeddings
)

def upload_resume(
    db: Session,
    file,
    user_id
):

    started_at = perf_counter()
    file_bytes = file.file.read()
    file_size = len(file_bytes)

    s3_key = (
        f"resumes/"
        f"{user_id}/"
        f"{uuid.uuid4()}_{file.filename}"
    )

    logger.info(
        (
            "resume_upload_started content_type=%s "
            "size_bytes=%s"
        ),
        file.content_type,
        file_size
    )

    try:
        # Upload to S3
        upload_file_to_s3(
            io.BytesIO(file_bytes),
            s3_key
        )

        # Extract text
        extracted_text = extract_text_from_pdf(
            io.BytesIO(file_bytes)
        )
    except Exception:
        logger.exception(
            (
                "resume_upload_processing_failed size_bytes=%s"
            ),
            file_size
        )
        raise

    # Create resume row
    resume = Resume(
        user_id=user_id,
        filename=file.filename,
        s3_key=s3_key,
        extracted_text=extracted_text
    )

    db.add(resume)

    db.commit()

    db.refresh(resume)

    # Chunk text
    chunks = chunk_resume_text(
        extracted_text
    )

    # Generate embeddings
    embeddings = generate_embeddings(
        chunks
    )

    # Store chunks
    for index, chunk in enumerate(chunks):

        resume_chunk = ResumeChunk(
            resume_id=resume.id,
            chunk_text=chunk,
            embedding=embeddings[index],
            chunk_order=index
        )

        db.add(resume_chunk)

    db.commit()

    logger.info(
        (
            "resume_upload_completed resume_id=%s "
            "chunks=%s extracted_chars=%s "
            "duration_ms=%s"
        ),
        resume.id,
        len(chunks),
        len(extracted_text or ""),
        int((perf_counter() - started_at) * 1000)
    )

    return resume
