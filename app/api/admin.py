# app/api/admin.py
from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.repositories.booking_repo import BookingRepository
from app.services.auth_service import AuthService
from app.utils.security import hash_password
from app.models.user import User
from bson import ObjectId
import re

router = APIRouter(prefix="/api/admin", tags=["管理员"])


def get_auth_service():
    db = get_db()
    repo = UserRepository(db)
    return AuthService(repo)


def is_valid_object_id(id_str):
    if not id_str:
        return False
    return bool(re.match(r'^[0-9a-fA-F]{24}$', id_str))


# ========== 教师审核 ==========

@router.get("/teachers/pending")
async def get_pending_teachers():
    service = get_auth_service()
    return await service.get_teachers_pending()


@router.post("/teachers/verify")
async def verify_teacher(user_id: str = Form(...)):
    service = get_auth_service()
    result = await service.verify_teacher(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/teachers/reject")
async def reject_teacher(user_id: str = Form(...)):
    service = get_auth_service()
    result = await service.delete_user(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ========== 管理员创建教师账号 ==========

@router.post("/teacher")
async def create_teacher(
        username: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        phone: str = Form(...),
        teacher_gender: str = Form(...),
        teacher_title: str = Form(...),
        teacher_specialty: str = Form(...)
):
    try:
        db = get_db()
        repo = UserRepository(db)

        existing = await repo.find_by_username(username)
        if existing:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "工号已存在"}
            )

        user = User(
            username=username,
            password=hash_password(password),
            name=name,
            phone=phone,
            role="teacher",
            teacher_gender=teacher_gender,
            teacher_title=teacher_title,
            teacher_specialty=teacher_specialty,
            teacher_verified=True,
            status="active"
        )

        await repo.create(user)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "教师账号创建成功"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"创建失败: {str(e)}"}
        )


# ========== 管理员创建学生账号 ==========

@router.post("/student")
async def create_student(
        username: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        phone: str = Form(...),
        student_gender: str = Form(...),
        student_class: str = Form(...),
        age: int = Form(...)
):
    try:
        db = get_db()
        repo = UserRepository(db)

        existing = await repo.find_by_username(username)
        if existing:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "学号已存在"}
            )

        user = User(
            username=username,
            password=hash_password(password),
            name=name,
            phone=phone,
            role="student",
            gender=student_gender,
            student_class=student_class,
            age=age,
            status="active"
        )

        await repo.create(user)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "学生账号创建成功"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"创建失败: {str(e)}"}
        )


# ========== 用户管理 ==========

@router.get("/teachers")
async def get_all_teachers():
    service = get_auth_service()
    return await service.get_all_teachers_full()


@router.get("/students")
async def get_all_students():
    service = get_auth_service()
    return await service.get_all_students()


@router.post("/users/{user_id}/enable")
async def enable_user(user_id: str):
    try:
        if not is_valid_object_id(user_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的用户ID"}
            )

        db = get_db()
        repo = UserRepository(db)
        user = await repo.find_by_id(user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "用户不存在"}
            )

        await repo.update(user_id, {"status": "active"})
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "用户已启用"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"操作失败: {str(e)}"}
        )


@router.post("/users/{user_id}/disable")
async def disable_user(user_id: str):
    try:
        if not is_valid_object_id(user_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的用户ID"}
            )

        db = get_db()
        repo = UserRepository(db)
        user = await repo.find_by_id(user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "用户不存在"}
            )
        if user.role == "admin":
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "不能禁用管理员账号"}
            )

        await repo.update(user_id, {"status": "inactive"})
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "用户已禁用"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"操作失败: {str(e)}"}
        )


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    try:
        if not is_valid_object_id(user_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的用户ID"}
            )

        db = get_db()
        repo = UserRepository(db)
        user = await repo.find_by_id(user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "用户不存在"}
            )
        if user.role == "admin":
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "不能删除管理员账号"}
            )

        await repo.delete_permanently(user_id)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "用户已删除"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )


# ========== 数据管理 ==========

@router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str):
    try:
        if not is_valid_object_id(booking_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的预约ID"}
            )

        db = get_db()
        repo = BookingRepository(db)
        booking = await repo.find_by_id(booking_id)
        if not booking:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "预约不存在"}
            )

        await repo.delete_permanently(booking_id)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "预约已删除"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )


@router.delete("/bookings/all")
async def delete_all_bookings():
    try:
        db = get_db()
        result = await db["bookings"].delete_many({})
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"已删除 {result.deleted_count} 条预约记录"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )