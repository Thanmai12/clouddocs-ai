from uuid import UUID

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, SessionLocal
from app.models import Document
from app.schemas import DocumentOut
from app.storage import upload_file
from app.processing import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"application/pdf", "text/plain"}


@router.post("", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only PDF and TXT files are supported.")

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(400, f"File exceeds {settings.max_upload_size_mb}MB limit.")

    r2_key = upload_file(file_bytes, file.filename, file.content_type)

    document = Document(
        filename=file.filename,
        r2_key=r2_key,
        content_type=file.content_type,
        size_bytes=len(file_bytes),
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Kick off async processing — the request returns immediately.
    background_tasks.add_task(process_document, str(document.id), SessionLocal)

    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found.")
    return document
