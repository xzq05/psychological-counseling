# app/api/bookings.py
from fastapi import APIRouter, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app.database import get_db
from app.repositories.booking_repo import BookingRepository
from app.repositories.user_repo import UserRepository
from app.services.booking_service import BookingService
from app.services.auth_service import AuthService

router = APIRouter(tags=["预约"])
templates = Jinja2Templates(directory="templates")


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
async def create_booking(
        student_id: str = Form(...),
        student_name: str = Form(...),
        student_phone: str = Form(...),
        student_gender: str = Form(...),
        student_age: int = Form(...),
        student_class: str = Form(...),
        booking_date: str = Form(...),
        booking_time: str = Form(...),
        consultation_type: str = Form(...),
        consultation_detail: str = Form(default=""),
        teacher_id: str = Form(default="")
):
    """学生创建预约"""
    service = get_booking_service()

    data = {
        "student_id": student_id,
        "student_name": student_name,
        "student_phone": student_phone,
        "student_gender": student_gender,
        "student_age": student_age,
        "student_class": student_class,
        "booking_date": booking_date,
        "booking_time": booking_time,
        "consultation_type": consultation_type,
        "consultation_detail": consultation_detail,
        "status": "待确认"
    }

    # 如果选择了老师，保存老师信息
    if teacher_id:
        data["teacher_id"] = teacher_id
        db = get_db()
        repo = UserRepository(db)
        teacher = await repo.find_by_id(teacher_id)
        if teacher:
            data["teacher_name"] = teacher.name

    return await service.create_booking(data)


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
        teacher_id: str = Form(...),
        teacher_name: str = Form(...),
        confirmed_date: str = Form(...),
        confirmed_time: str = Form(...),
        room: str = Form(...)
):
    """教师确认预约"""
    service = get_booking_service()
    return await service.confirm_booking(
        booking_id, teacher_id, teacher_name, confirmed_date, confirmed_time, room
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