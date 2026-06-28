# app/api/bookings.py
from fastapi import APIRouter, HTTPException, Request, Form, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.repositories.booking_repo import BookingRepository
from app.repositories.user_repo import UserRepository
from app.services.booking_service import BookingService
from app.services.auth_service import AuthService

router = APIRouter(tags=["预约"])
templates = Jinja2Templates(directory="templates")


# ========== 请求模型 ==========
class BookingCreateRequest(BaseModel):
    student_id: str
    student_name: str
    student_phone: str
    student_gender: str
    student_age: int
    student_class: str
    booking_date: str
    booking_time: str
    consultation_type: str
    consultation_detail: Optional[str] = ""
    teacher_id: Optional[str] = ""


class BookingConfirmRequest(BaseModel):
    teacher_id: str
    teacher_name: str
    confirmed_date: str
    confirmed_time: str
    room: str


def get_booking_service():
    db = get_db()
    repo = BookingRepository(db)
    return BookingService(repo)


def get_auth_service():
    db = get_db()
    repo = UserRepository(db)
    return AuthService(repo)


# ========== 页面路由 ==========
@router.get("/student", response_class=HTMLResponse)
async def student_dashboard(request: Request):
    return templates.TemplateResponse("student_dashboard.html", {"request": request})


@router.get("/teacher", response_class=HTMLResponse)
async def teacher_dashboard(request: Request):
    return templates.TemplateResponse("teacher_dashboard.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


# ========== API 路由 ==========
@router.get("/api/teachers/list")
async def get_teachers_list():
    """获取所有心理老师列表（供学生选择）"""
    service = get_auth_service()
    return await service.get_all_teachers()


@router.post("/api/bookings")
async def create_booking(request: BookingCreateRequest):
    """学生创建预约 - JSON 格式"""
    try:
        service = get_booking_service()

        data = {
            "student_id": request.student_id,
            "student_name": request.student_name,
            "student_phone": request.student_phone,
            "student_gender": request.student_gender,
            "student_age": request.student_age,
            "student_class": request.student_class,
            "booking_date": request.booking_date,
            "booking_time": request.booking_time,
            "consultation_type": request.consultation_type,
            "consultation_detail": request.consultation_detail or "",
            "status": "待确认"
        }

        # 如果选择了老师，保存老师信息
        if request.teacher_id:
            data["teacher_id"] = request.teacher_id
            db = get_db()
            repo = UserRepository(db)
            teacher = await repo.find_by_id(request.teacher_id)
            if teacher:
                data["teacher_name"] = teacher.name

        result = await service.create_booking(data)

        # 确保返回的是 JSON 可序列化的数据
        return JSONResponse(
            status_code=200 if result.get("success") else 400,
            content=result
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"服务器错误: {str(e)}"}
        )


@router.get("/api/bookings/student/{student_id}")
async def get_student_bookings(student_id: str):
    """学生查看自己的预约"""
    service = get_booking_service()
    return await service.get_student_bookings(student_id)


@router.get("/api/bookings/pending")
async def get_pending_bookings():
    """教师查看待确认预约"""
    service = get_booking_service()
    return await service.get_pending_bookings()


@router.get("/api/bookings/all")
async def get_all_bookings():
    """管理员查看所有预约"""
    service = get_booking_service()
    return await service.get_all_bookings()


@router.get("/api/bookings/today")
async def get_today_bookings(date: str = Query(..., description="日期 YYYY-MM-DD")):
    """获取某天所有预约"""
    service = get_booking_service()
    return await service.get_today_bookings(date)


@router.post("/api/bookings/{booking_id}/confirm")
async def confirm_booking(
        booking_id: str,
        request: Request
):
    """教师确认预约 - JSON 格式"""
    try:
        data = await request.json()
        service = get_booking_service()
        result = await service.confirm_booking(
            booking_id,
            data.get("teacher_id"),
            data.get("teacher_name"),
            data.get("confirmed_date"),
            data.get("confirmed_time"),
            data.get("room")
        )
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"确认失败: {str(e)}"}
        )


@router.post("/api/bookings/{booking_id}/reject")
async def reject_booking(booking_id: str):
    """教师拒绝预约"""
    service = get_booking_service()
    return await service.reject_booking(booking_id)


@router.delete("/api/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str):
    """学生取消预约"""
    service = get_booking_service()
    return await service.cancel_booking(booking_id)


@router.post("/api/bookings/{booking_id}/complete")
async def complete_booking(booking_id: str):
    """完成咨询"""
    service = get_booking_service()
    return await service.complete_booking(booking_id)