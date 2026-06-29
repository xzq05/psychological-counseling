# app/models/user.py
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    username: str
    password: str
    name: str
    phone: str
    role: str = "student"

    student_class: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    teacher_title: Optional[str] = None
    teacher_specialty: Optional[str] = None
    teacher_gender: Optional[str] = None
    teacher_verified: bool = False

    status: str = "active"

    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

    created_at: datetime = Field(default_factory=get_beijing_time)
    updated_at: datetime = Field(default_factory=get_beijing_time)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )