# app/api/admin.py
from fastapi import APIRouter, HTTPException, Form, Query
from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

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
        teacher_title: str = Form(...),
        teacher_specialty: str = Form(...)
):
    """管理员直接创建教师账号（无需审核）"""
    service = get_auth_service()
    data = {
        "username": username,
        "password": password,
        "name": name,
        "phone": phone,
        "teacher_title": teacher_title,
        "teacher_specialty": teacher_specialty
    }
    # 管理员创建的教师直接审核通过
    result = await service.register_teacher(data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    # 获取刚创建的教师并自动审核通过
    db = get_db()
    repo = UserRepository(db)
    user = await repo.find_by_username(username)
    if user:
        await repo.verify_teacher(user.id)

    return result


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


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """禁用用户"""
    service = get_auth_service()
    result = await service.delete_user(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/users/{user_id}/activate")
async def activate_user(user_id: str):
    """激活用户"""
    service = get_auth_service()
    result = await service.update_user(user_id, {"status": "active"})
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str):
    """禁用用户"""
    service = get_auth_service()
    result = await service.update_user(user_id, {"status": "inactive"})
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result