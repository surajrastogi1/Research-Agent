from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


# Source Schemas
class SourceResponse(BaseModel):
    id: UUID
    title: Optional[str] = None
    url: str
    content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Research Schemas
class ResearchCreate(BaseModel):
    question: str


class ResearchResponse(BaseModel):
    id: UUID
    user_id: UUID
    question: str
    status: str
    report: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    sources: List[SourceResponse] = []

    class Config:
        from_attributes = True