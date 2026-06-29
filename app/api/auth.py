# app/api/auth.py
from fastapi import APIRouter, HTTPException, Request, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.utils.jwt_util import create_access_token

router = APIRouter(tags=["认证"])
templates = Jinja2Templates(directory="templates")


def get_auth_service():
    db = get_db()
    repo = UserRepository(db)
    return AuthService(repo)


# ========== 请求模型 ==========
class StudentRegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    phone: str
    student_class: str
    age: int
    gender: str


class TeacherRegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    phone: str
    teacher_title: str
    teacher_specialty: str
    teacher_gender: str  # 新增


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    username: str
    phone: str
    gender: str
    class_name: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


# ========== 首页 ==========
@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ========== Admin 独立登录 ==========
@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@router.get("/admin/change-password", response_class=HTMLResponse)
async def admin_change_password_page(request: Request):
    return templates.TemplateResponse("admin_change_password.html", {"request": request})


@router.post("/api/auth/admin/login")
async def admin_login(request: LoginRequest):
    service = get_auth_service()
    result = await service.login(request.username, request.password)

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])

    if result["role"] != "admin":
        raise HTTPException(status_code=403, detail="请使用管理员账号登录")

    token = create_access_token({
        "sub": result["username"],
        "user_id": result["user_id"],
        "role": result["role"]
    })

    return {
        "success": True,
        "token": token,
        "user_id": result["user_id"],
        "username": result["username"],
        "name": result["name"],
        "role": result["role"]
    }


# ========== 学生端页面 ==========
@router.get("/student/login", response_class=HTMLResponse)
async def student_login_page(request: Request):
    return templates.TemplateResponse("student_login.html", {"request": request})


@router.get("/student/register", response_class=HTMLResponse)
async def student_register_page(request: Request):
    return templates.TemplateResponse("student_register.html", {"request": request})


@router.get("/student/forgot-password", response_class=HTMLResponse)
async def student_forgot_password_page(request: Request):
    return templates.TemplateResponse("student_forgot_password.html", {"request": request})


@router.get("/student/change-password", response_class=HTMLResponse)
async def student_change_password_page(request: Request):
    return templates.TemplateResponse("student_change_password.html", {"request": request})


# ========== 教师端页面 ==========
@router.get("/teacher/login", response_class=HTMLResponse)
async def teacher_login_page(request: Request):
    return templates.TemplateResponse("teacher_login.html", {"request": request})


@router.get("/teacher/register", response_class=HTMLResponse)
async def teacher_register_page(request: Request):
    return templates.TemplateResponse("teacher_register.html", {"request": request})


@router.get("/teacher/forgot-password", response_class=HTMLResponse)
async def teacher_forgot_password_page(request: Request):
    return templates.TemplateResponse("teacher_forgot_password.html", {"request": request})


@router.get("/teacher/change-password", response_class=HTMLResponse)
async def teacher_change_password_page(request: Request):
    return templates.TemplateResponse("teacher_change_password.html", {"request": request})


# ========== 学生 API（JSON 格式） ==========
@router.post("/api/auth/student/login")
async def student_login(request: LoginRequest):
    service = get_auth_service()
    result = await service.login(request.username, request.password)

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])

    if result["role"] != "student":
        raise HTTPException(status_code=403, detail="请使用学生账号登录")

    token = create_access_token({
        "sub": result["username"],
        "user_id": result["user_id"],
        "role": result["role"]
    })

    return {
        "success": True,
        "token": token,
        "user_id": result["user_id"],
        "username": result["username"],
        "name": result["name"],
        "role": result["role"]
    }


@router.post("/api/auth/student/register")
async def register_student(request: StudentRegisterRequest):
    """学生注册 API - JSON 格式"""
    try:
        service = get_auth_service()
        data = {
            "username": request.username,
            "password": request.password,
            "name": request.name,
            "phone": request.phone,
            "student_class": request.student_class,
            "age": request.age,
            "gender": request.gender
        }
        result = await service.register_student(data)

        return JSONResponse(
            status_code=200 if result["success"] else 400,
            content=result
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"服务器错误: {str(e)}"}
        )


# ========== 教师 API（JSON 格式） ==========
@router.post("/api/auth/teacher/login")
async def teacher_login(request: LoginRequest):
    service = get_auth_service()
    result = await service.login(request.username, request.password)

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])

    if result["role"] != "teacher":
        raise HTTPException(status_code=403, detail="请使用教师账号登录")

    token = create_access_token({
        "sub": result["username"],
        "user_id": result["user_id"],
        "role": result["role"]
    })

    return {
        "success": True,
        "token": token,
        "user_id": result["user_id"],
        "username": result["username"],
        "name": result["name"],
        "role": result["role"]
    }


@router.post("/api/auth/teacher/register")
async def register_teacher(request: TeacherRegisterRequest):
    """教师注册 API - JSON 格式（含性别）"""
    try:
        service = get_auth_service()
        data = {
            "username": request.username,
            "password": request.password,
            "name": request.name,
            "phone": request.phone,
            "teacher_title": request.teacher_title,
            "teacher_specialty": request.teacher_specialty,
            "teacher_gender": request.teacher_gender
        }
        result = await service.register_teacher(data)

        return JSONResponse(
            status_code=200 if result["success"] else 400,
            content=result
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"服务器错误: {str(e)}"}
        )


# ========== 通用密码重置 ==========
@router.post("/api/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """通过手机号、性别、班级验证身份，生成临时密码"""
    service = get_auth_service()
    result = await service.reset_password_by_info(
        request.username,
        request.phone,
        request.gender,
        request.class_name
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ========== 修改密码 ==========
@router.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest):
    """修改密码，需要验证旧密码"""
    service = get_auth_service()
    result = await service.change_password(
        request.username,
        request.old_password,
        request.new_password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ========== 获取教师列表 ==========
@router.get("/api/auth/teachers")
async def get_teachers():
    service = get_auth_service()
    return await service.get_all_teachers()