# app/models/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    # 基本信息
    username: str
    password: str
    name: str
    phone: str
    role: str = "student"  # student / teacher / admin

    # 学生专属
    student_class: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    # 教师专属
    teacher_title: Optional[str] = None
    teacher_specialty: Optional[str] = None
    teacher_verified: bool = False  # 教师账号是否通过审核（默认False）

    # 状态
    status: str = "active"  # active / inactive / pending_verification

    # 密码重置
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )