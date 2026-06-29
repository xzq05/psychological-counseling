# app/services/auth_service.py
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.utils.security import hash_password, verify_password
from datetime import datetime, timedelta
import secrets
import random


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_student(self, data: dict) -> dict:
        """学生注册"""
        existing = await self.user_repo.find_by_username(data.get("username"))
        if existing:
            return {"success": False, "message": "学号已存在"}

        user = User(
            username=data["username"],
            password=hash_password(data["password"]),
            name=data["name"],
            phone=data["phone"],
            role="student",
            student_class=data.get("student_class"),
            age=data.get("age"),
            gender=data.get("gender")
        )
        await self.user_repo.create(user)
        return {"success": True, "message": "注册成功，请前往登录"}

    async def register_teacher(self, data: dict) -> dict:
        """教师注册（需要管理员审核）- 含性别"""
        existing = await self.user_repo.find_by_username(data.get("username"))
        if existing:
            return {"success": False, "message": "工号已存在"}

        user = User(
            username=data["username"],
            password=hash_password(data["password"]),
            name=data["name"],
            phone=data["phone"],
            role="teacher",
            teacher_title=data.get("teacher_title"),
            teacher_specialty=data.get("teacher_specialty"),
            teacher_gender=data.get("teacher_gender"),  # 新增
            teacher_verified=False,
            status="active"
        )
        await self.user_repo.create(user)
        return {"success": True, "message": "注册成功，请等待管理员审核"}

    async def verify_teacher(self, user_id: str) -> dict:
        """管理员审核通过教师账号"""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}
        if user.role != "teacher":
            return {"success": False, "message": "该用户不是教师"}

        await self.user_repo.verify_teacher(user_id)
        return {"success": True, "message": "教师账号审核通过"}

    async def login(self, username: str, password: str) -> dict:
        """通用登录验证"""
        user = await self.user_repo.find_by_username(username)
        if not user:
            return {"success": False, "message": "用户名或密码错误"}

        if not verify_password(password, user.password):
            return {"success": False, "message": "用户名或密码错误"}

        # 检查教师账号是否已审核
        if user.role == "teacher":
            is_verified = getattr(user, 'teacher_verified', False)
            if not is_verified:
                return {"success": False, "message": "账号正在审核中，请等待管理员审核"}

        # 检查账号状态
        if user.status != "active":
            return {"success": False, "message": "账号已被禁用，请联系管理员"}

        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role
        }

    async def reset_password_by_info(self, username: str, phone: str, gender: str, class_name: str) -> dict:
        """通过验证信息重置密码，生成6位随机数字临时密码"""
        user = await self.user_repo.find_by_username(username)
        if not user:
            return {"success": False, "message": "用户不存在"}

        # 验证手机号
        if user.phone != phone:
            return {"success": False, "message": "手机号不匹配"}

        # 根据角色验证不同字段
        if user.role == "student":
            if user.gender != gender:
                return {"success": False, "message": "性别不匹配"}
            if user.student_class != class_name:
                return {"success": False, "message": "班级不匹配"}
        elif user.role == "teacher":
            # 教师使用 teacher_gender 字段验证性别
            teacher_gender = getattr(user, 'teacher_gender', None)
            if teacher_gender != gender:
                return {"success": False, "message": "性别不匹配"}
            if user.teacher_title != class_name:
                return {"success": False, "message": "职称不匹配"}
        else:
            return {"success": False, "message": "该账号类型不支持此操作"}

        # 生成6位随机数字密码
        temp_password = ''.join(random.choices('0123456789', k=6))

        # 更新密码
        await self.user_repo.update(user.id, {
            "password": hash_password(temp_password)
        })

        return {
            "success": True,
            "message": "密码重置成功",
            "temp_password": temp_password
        }

    async def change_password(self, username: str, old_password: str, new_password: str) -> dict:
        """修改密码，验证旧密码"""
        user = await self.user_repo.find_by_username(username)
        if not user:
            return {"success": False, "message": "用户不存在"}

        # 验证旧密码
        if not verify_password(old_password, user.password):
            return {"success": False, "message": "原密码错误"}

        # 更新密码
        await self.user_repo.update(user.id, {
            "password": hash_password(new_password)
        })

        return {"success": True, "message": "密码修改成功"}

    async def get_all_teachers(self) -> list:
        """获取所有已审核的教师（供学生选择）"""
        teachers = await self.user_repo.find_by_role("teacher")
        result = []
        for t in teachers:
            is_verified = getattr(t, 'teacher_verified', False)
            if is_verified:
                result.append({
                    "id": t.id,
                    "name": t.name,
                    "title": t.teacher_title,
                    "specialty": t.teacher_specialty,
                    "gender": getattr(t, 'teacher_gender', '未设置'),
                    "verified": True
                })
        return result

    async def get_teachers_pending(self) -> list:
        """获取待审核的教师"""
        teachers = await self.user_repo.find_teachers_pending()
        result = []
        for t in teachers:
            result.append({
                "id": t.id,
                "username": t.username,
                "name": t.name,
                "phone": t.phone,
                "teacher_title": t.teacher_title,
                "teacher_specialty": t.teacher_specialty,
                "teacher_gender": getattr(t, 'teacher_gender', '未设置'),
                "teacher_verified": getattr(t, 'teacher_verified', False)
            })
        return result

    async def get_all_students(self) -> list:
        """获取所有学生"""
        students = await self.user_repo.find_all_students()
        result = []
        for s in students:
            result.append({
                "id": s.id,
                "username": s.username,
                "name": s.name,
                "phone": s.phone,
                "student_class": s.student_class,
                "age": s.age,
                "gender": s.gender,
                "status": s.status
            })
        return result

    async def get_all_teachers_full(self) -> list:
        """获取所有教师（包括待审核）- 含性别"""
        teachers = await self.user_repo.find_all_teachers()
        result = []
        for t in teachers:
            result.append({
                "id": t.id,
                "username": t.username,
                "name": t.name,
                "phone": t.phone,
                "teacher_title": t.teacher_title,
                "teacher_specialty": t.teacher_specialty,
                "teacher_gender": getattr(t, 'teacher_gender', '未设置'),
                "teacher_verified": getattr(t, 'teacher_verified', False),
                "status": t.status
            })
        return result

    async def get_user_by_id(self, user_id: str):
        return await self.user_repo.find_by_id(user_id)

    async def update_user(self, user_id: str, data: dict):
        await self.user_repo.update(user_id, data)
        return {"success": True, "message": "更新成功"}

    async def delete_user(self, user_id: str):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}
        if user.role == "admin":
            return {"success": False, "message": "不能删除管理员账号"}

        await self.user_repo.delete(user_id)
        return {"success": True, "message": "用户已禁用"}

    async def request_password_reset(self, username: str) -> dict:
        user = await self.user_repo.find_by_username(username)
        if not user:
            return {"success": False, "message": "用户不存在"}

        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(minutes=30)

        await self.user_repo.update(user.id, {
            "reset_token": token,
            "reset_token_expires": expires
        })

        return {
            "success": True,
            "message": "密码重置链接已生成",
            "token": token
        }

    async def reset_password(self, token: str, new_password: str) -> dict:
        user = await self.user_repo.find_by_reset_token(token)
        if not user:
            return {"success": False, "message": "无效的重置链接"}

        if user.reset_token_expires < datetime.now():
            return {"success": False, "message": "重置链接已过期"}

        await self.user_repo.update(user.id, {
            "password": hash_password(new_password),
            "reset_token": None,
            "reset_token_expires": None
        })

        return {"success": True, "message": "密码重置成功"}