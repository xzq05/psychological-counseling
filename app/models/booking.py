# app/models/booking.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class Booking(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    # 学生信息
    student_id: str
    student_name: str
    student_phone: str
    student_gender: str
    student_age: int
    student_class: str

    # 预约信息
    booking_date: str
    booking_time: str
    consultation_type: str
    consultation_detail: Optional[str] = None

    # 教师安排
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    confirmed_date: Optional[str] = None
    confirmed_time: Optional[str] = None
    room: Optional[str] = None

    # 状态
    queue_number: int = 0
    status: str = "待确认"

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )