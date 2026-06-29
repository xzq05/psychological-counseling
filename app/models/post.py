# app/models/post.py
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


class Post(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    title: str
    content: str
    category: str = "其他"
    author: str
    images: List[str] = []  # 图片URL列表
    likes: int = 0
    comments_count: int = 0

    created_at: datetime = Field(default_factory=get_beijing_time)
    updated_at: datetime = Field(default_factory=get_beijing_time)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )