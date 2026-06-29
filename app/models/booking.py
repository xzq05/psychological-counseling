# app/models/booking.py
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


class Booking(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    student_id: str
    student_name: str
    student_phone: str
    student_gender: str
    student_age: int
    student_class: str

    booking_date: str
    booking_time: str
    consultation_type: str
    consultation_detail: Optional[str] = None

    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    confirmed_date: Optional[str] = None
    confirmed_time: Optional[str] = None
    room: Optional[str] = None

    queue_number: int = 0
    status: str = "待确认"

    created_at: datetime = Field(default_factory=get_beijing_time)
    updated_at: datetime = Field(default_factory=get_beijing_time)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )