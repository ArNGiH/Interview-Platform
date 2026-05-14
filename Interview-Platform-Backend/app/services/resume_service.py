import io
import uuid

from sqlalchemy.orm import Session
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


DUMMY_USER_ID = "fb341b60-f05b-4cc0-9430-38a7a0b1f524"


def upload_resume(
    db: Session,
    file
):

    file_bytes = file.file.read()

    s3_key = (
        f"resumes/"
        f"{DUMMY_USER_ID}/"
        f"{uuid.uuid4()}_{file.filename}"
    )

    # Upload to S3
    upload_file_to_s3(
        io.BytesIO(file_bytes),
        s3_key
    )

    # Extract text
    extracted_text = extract_text_from_pdf(
        io.BytesIO(file_bytes)
    )

    # Create resume row
    resume = Resume(
        user_id=DUMMY_USER_ID,
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

    return resume