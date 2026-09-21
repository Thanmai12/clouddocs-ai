from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import Document
from app.schemas import QueryRequest, QueryResponse
from app.rag import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/hour")
def query_document(request: Request, payload: QueryRequest, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == payload.document_id).first()
    if not document:
        raise HTTPException(404, "Document not found.")
    if document.status != "ready":
        raise HTTPException(409, f"Document is not ready yet (status: {document.status}).")

    result = answer_question(str(document.id), payload.question)
    return result
