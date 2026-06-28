# app/api/admin.py
from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.utils.security import hash_password
from app.models.user import User

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
        teacher_gender: str = Form(...),  # 新增
        teacher_title: str = Form(...),
        teacher_specialty: str = Form(...)
):
    """管理员直接创建教师账号（无需审核）- 含性别"""
    try:
        db = get_db()
        repo = UserRepository(db)

        # 检查用户名是否已存在
        existing = await repo.find_by_username(username)
        if existing:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "工号已存在"}
            )

        # 创建教师用户
        user = User(
            username=username,
            password=hash_password(password),
            name=name,
            phone=phone,
            role="teacher",
            teacher_gender=teacher_gender,
            teacher_title=teacher_title,
            teacher_specialty=teacher_specialty,
            teacher_verified=True,  # 管理员创建的教师直接审核通过
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