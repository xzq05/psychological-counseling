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

router = APIRouter(prefix="/api/admin", tags=["管理员"])


def get_auth_service():
    db = get_db()
    repo = UserRepository(db)
    return AuthService(repo)


# ========== 教师审核 ==========

@router.get("/teachers/pending")
async def get_pending_teachers():
    """获取待审核的教师列表"""
    service = get_auth_service()
    return await service.get_teachers_pending()


@router.post("/teachers/verify")
async def verify_teacher(user_id: str = Form(...)):
    """审核通过教师账号"""
    service = get_auth_service()
    result = await service.verify_teacher(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/teachers/reject")
async def reject_teacher(user_id: str = Form(...)):
    """拒绝教师注册申请（直接删除账号）"""
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
    """管理员直接创建教师账号（无需审核）- 含性别"""
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
    """管理员直接创建学生账号"""
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
    """获取所有教师（包括待审核）"""
    service = get_auth_service()
    return await service.get_all_teachers_full()


@router.get("/students")
async def get_all_students():
    """获取所有学生"""
    service = get_auth_service()
    return await service.get_all_students()


@router.post("/users/{user_id}/enable")
async def enable_user(user_id: str):
    """启用用户"""
    try:
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
    """禁用用户"""
    try:
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
    """删除用户（永久删除）"""
    try:
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
    """删除预约记录"""
    try:
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
    """删除所有预约记录（慎用）"""
    try:
        db = get_db()
        repo = BookingRepository(db)
        await repo.delete_all()
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "所有预约已删除"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除失败: {str(e)}"}
        )