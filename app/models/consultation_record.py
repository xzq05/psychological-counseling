# app/models/consultation_record.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Content(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None


class ItemScore(BaseModel):
    question_id: str
    score: int


class ScaleResult(BaseModel):
    scale_type: str
    score: int
    severity: Optional[str] = None
    items: List[ItemScore] = []


class ConsultationRecord(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    booking_id: str
    visitor_id: str
    counselor_id: str
    session_number: int
    record_type: str
    content: Content
    scale_results: List[ScaleResult] = []
    supervisor_comment: Optional[str] = None
    is_shared: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True