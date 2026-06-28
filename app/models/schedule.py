# app/models/schedule.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TimeSlot(BaseModel):
    start_time: str
    end_time: str
    status: str = "AVAILABLE"
    booking_id: Optional[str] = None


class Schedule(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    counselor_id: str
    date: str  # 存储为字符串 "2026-01-15"
    time_slots: List[TimeSlot] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True