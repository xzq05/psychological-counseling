# app/models/message.py
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


# 获取东八区时间
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


class Message(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    sender_id: str
    sender_name: str
    sender_role: str
    receiver_id: str
    receiver_name: str
    receiver_role: str

    content: str
    is_read: bool = False
    read_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=get_beijing_time)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class Announcement(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    title: str
    content: str
    author: str
    is_active: bool = True
    priority: int = 0

    created_at: datetime = Field(default_factory=get_beijing_time)
    updated_at: datetime = Field(default_factory=get_beijing_time)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )