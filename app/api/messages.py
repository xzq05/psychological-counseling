# app/api/messages.py - 添加Admin聊天功能
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.repositories.message_repo import MessageRepository, AnnouncementRepository
from app.models.message import Message, Announcement
from datetime import datetime

router = APIRouter(tags=["消息"])
templates = Jinja2Templates(directory="templates")


def get_message_repo():
    db = get_db()
    return MessageRepository(db)


def get_announcement_repo():
    db = get_db()
    return AnnouncementRepository(db)


class SendMessageRequest(BaseModel):
    sender_id: str
    sender_name: str
    sender_role: str
    receiver_id: str
    receiver_name: str
    receiver_role: str
    content: str


class AnnouncementCreateRequest(BaseModel):
    title: str
    content: str
    author: str
    priority: int = 0


@router.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request):
    return templates.TemplateResponse("messages.html", {"request": request})


@router.get("/api/announcements")
async def get_announcements():
    repo = get_announcement_repo()
    return await repo.find_all_active()


@router.get("/api/messages/unread")
async def get_unread_count(receiver_id: str = Query(...)):
    try:
        repo = get_message_repo()
        count = await repo.find_unread_count(receiver_id)
        return {"unread_count": count}
    except Exception as e:
        return {"unread_count": 0}


@router.get("/api/messages/chats/{user_id}")
async def get_chat_users(user_id: str):
    try:
        repo = get_message_repo()
        user_ids = await repo.get_chat_users(user_id)

        from app.database import get_db
        from app.repositories.user_repo import UserRepository
        db = get_db()
        user_repo = UserRepository(db)

        users = []
        for uid in user_ids:
            user = await user_repo.find_by_id(uid)
            if user:
                messages = await repo.find_by_users(user_id, uid, limit=1)
                last_message = messages[0].content if messages else ""
                last_time = messages[0].created_at if messages else ""
                if isinstance(last_time, datetime):
                    last_time = last_time.isoformat()
                elif not last_time:
                    last_time = ""

                users.append({
                    "id": user.id,
                    "name": user.name,
                    "role": user.role,
                    "last_message": last_message,
                    "last_time": last_time
                })

        # 如果是Admin，获取所有用户（即使没有聊天记录）
        from app.repositories.user_repo import UserRepository
        db = get_db()
        user_repo = UserRepository(db)
        admin = await user_repo.find_by_id(user_id)

        if admin and admin.role == "admin":
            # 获取所有活跃用户
            all_users = await user_repo.find_all()
            existing_ids = [u["id"] for u in users]
            for u in all_users:
                if u.id != user_id and u.id not in existing_ids:
                    users.append({
                        "id": u.id,
                        "name": u.name,
                        "role": u.role,
                        "last_message": "点击开始聊天",
                        "last_time": ""
                    })

        return sorted(users, key=lambda x: x["last_time"], reverse=True)
    except Exception as e:
        return []


@router.get("/api/messages/{user1_id}/{user2_id}")
async def get_messages(user1_id: str, user2_id: str, limit: int = 50):
    try:
        repo = get_message_repo()
        messages = await repo.find_by_users(user1_id, user2_id, limit)
        await repo.mark_all_read(user1_id, user2_id)

        result = []
        for m in messages:
            data = m.model_dump()
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'read_at' in data and data['read_at'] and isinstance(data['read_at'], datetime):
                data['read_at'] = data['read_at'].isoformat()
            result.append(data)
        return result
    except Exception as e:
        return []


@router.post("/api/messages/send")
async def send_message(request: SendMessageRequest):
    try:
        repo = get_message_repo()
        message = Message(
            sender_id=request.sender_id,
            sender_name=request.sender_name,
            sender_role=request.sender_role,
            receiver_id=request.receiver_id,
            receiver_name=request.receiver_name,
            receiver_role=request.receiver_role,
            content=request.content
        )
        result = await repo.create(message)

        data = result.model_dump()
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "消息发送成功", "data": data}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"发送失败: {str(e)}"}
        )