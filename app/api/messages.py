# app/api/messages.py
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


# ========== 请求模型 ==========
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


# ========== 页面路由 ==========
@router.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request):
    """消息页面"""
    return templates.TemplateResponse("messages.html", {"request": request})


# ========== API ==========

@router.get("/api/announcements")
async def get_announcements():
    """获取所有活跃公告"""
    repo = get_announcement_repo()
    return await repo.find_all_active()


@router.get("/api/announcements/all")
async def get_all_announcements():
    """获取所有公告（管理员用）"""
    repo = get_announcement_repo()
    return await repo.find_all()


@router.post("/api/announcements")
async def create_announcement(request: AnnouncementCreateRequest):
    """创建公告（管理员用）"""
    try:
        repo = get_announcement_repo()
        announcement = Announcement(
            title=request.title,
            content=request.content,
            author=request.author,
            priority=request.priority,
            is_active=True
        )
        result = await repo.create(announcement)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "公告创建成功", "data": result.model_dump()}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"创建失败: {str(e)}"}
        )


@router.put("/api/announcements/{announcement_id}")
async def update_announcement(announcement_id: str, request: AnnouncementCreateRequest):
    """更新公告"""
    try:
        repo = get_announcement_repo()
        data = {
            "title": request.title,
            "content": request.content,
            "author": request.author,
            "priority": request.priority
        }
        await repo.update(announcement_id, data)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "公告已更新"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新失败: {str(e)}"}
        )


@router.delete("/api/announcements/{announcement_id}")
async def delete_announcement(announcement_id: str):
    """删除公告"""
    try:
        repo = get_announcement_repo()
        await repo.delete(announcement_id)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "公告已删除"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )


@router.get("/api/messages/unread")
async def get_unread_count(receiver_id: str = Query(...)):
    """获取未读消息数量"""
    repo = get_message_repo()
    count = await repo.find_unread_count(receiver_id)
    return {"unread_count": count}


@router.get("/api/messages/chats/{user_id}")
async def get_chat_users(user_id: str):
    """获取与用户聊过天的所有用户"""
    repo = get_message_repo()
    user_ids = await repo.get_chat_users(user_id)

    # 获取用户信息
    from app.database import get_db
    from app.repositories.user_repo import UserRepository
    db = get_db()
    user_repo = UserRepository(db)

    users = []
    for uid in user_ids:
        user = await user_repo.find_by_id(uid)
        if user:
            # 获取最后一条消息
            messages = await repo.find_by_users(user_id, uid, limit=1)
            last_message = messages[0].content if messages else ""
            last_time = messages[0].created_at.isoformat() if messages else ""

            users.append({
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "last_message": last_message,
                "last_time": last_time
            })

    return sorted(users, key=lambda x: x["last_time"], reverse=True)


@router.get("/api/messages/{user1_id}/{user2_id}")
async def get_messages(user1_id: str, user2_id: str, limit: int = 50):
    """获取两个用户之间的聊天记录"""
    repo = get_message_repo()
    messages = await repo.find_by_users(user1_id, user2_id, limit)

    # 标记已读
    await repo.mark_all_read(user1_id, user2_id)

    return [m.model_dump() for m in messages]


@router.post("/api/messages/send")
async def send_message(request: SendMessageRequest):
    """发送消息"""
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
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "消息发送成功", "data": result.model_dump()}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"发送失败: {str(e)}"}
        )