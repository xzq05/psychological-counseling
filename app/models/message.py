# app/models/message.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class Message(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    # 发送者和接收者
    sender_id: str
    sender_name: str
    sender_role: str  # student / teacher / admin
    receiver_id: str
    receiver_name: str
    receiver_role: str  # student / teacher / admin

    # 消息内容
    content: str
    is_read: bool = False
    read_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.now)

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
    priority: int = 0  # 0=普通, 1=重要, 2=紧急

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )