from datetime import datetime
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    document_id: UUID
    question: str


class SourcePassage(BaseModel):
    text: str
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourcePassage]
    grounded: bool
