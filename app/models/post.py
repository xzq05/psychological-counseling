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
    author_id: str
    author_role: str = "student"  # student / teacher / admin
    likes: int = 0
    liked_by: List[str] = []  # 存储点赞用户的ID
    comments: List[dict] = []
    comments_count: int = 0

    created_at: datetime = Field(default_factory=get_beijing_time)
    updated_at: datetime = Field(default_factory=get_beijing_time)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )