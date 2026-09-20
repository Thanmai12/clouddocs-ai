import io
from datetime import datetime

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models import Document
from app.storage import download_file
from app.vectorstore import index_chunks


def extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Simple sliding-window character chunking with overlap."""
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def _set_status(db: Session, document: Document, status: str, error: str | None = None):
    document.status = status
    document.error_message = error
    document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(document)


def process_document(document_id: str, db_session_factory) -> None:
    """
    Runs as a FastAPI BackgroundTask right after upload.
    Takes a session factory (not a live session) since background tasks
    run outside the request's own DB session lifecycle.
    """
    db: Session = db_session_factory()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        _set_status(db, document, "extracting")
        file_bytes = download_file(document.r2_key)
        text = extract_text(file_bytes, document.content_type)

        if not text.strip():
            _set_status(db, document, "failed", "No extractable text found in document.")
            return

        _set_status(db, document, "chunking")
        chunks = chunk_text(text)

        _set_status(db, document, "embedding")
        # embedding happens inside index_chunks (sentence-transformers, local, free)

        _set_status(db, document, "indexing")
        chunk_count = index_chunks(str(document.id), chunks)

        document.chunk_count = chunk_count
        _set_status(db, document, "ready")

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            _set_status(db, document, "failed", str(exc))
    finally:
        db.close()
