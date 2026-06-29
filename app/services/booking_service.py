# app/services/booking_service.py
from app.models.booking import Booking
from app.repositories.booking_repo import BookingRepository
from app.models.message import Message
from datetime import datetime


class BookingService:
    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    async def create_booking(self, data: dict) -> dict:
        """学生创建预约 - 自动创建系统消息"""
        try:
            booking = Booking(**data)
            saved = await self.booking_repo.create(booking)

            # ===== 自动发送系统消息给老师 =====
            from app.database import get_db
            from app.repositories.message_repo import MessageRepository
            from app.repositories.user_repo import UserRepository

            db = get_db()
            message_repo = MessageRepository(db)
            user_repo = UserRepository(db)

            teacher_id = data.get("teacher_id")
            if teacher_id:
                teacher = await user_repo.find_by_id(teacher_id)
                if teacher:
                    student = await user_repo.find_by_id(data.get("student_id"))
                    student_name = student.name if student else data.get("student_name", "学生")

                    # 发送给老师
                    teacher_msg = Message(
                        sender_id=data.get("student_id"),
                        sender_name=student_name,
                        sender_role="student",
                        receiver_id=teacher_id,
                        receiver_name=teacher.name,
                        receiver_role="teacher",
                        content=f"📋 预约通知：{student_name} 已预约心理咨询\n"
                                f"📅 日期：{data.get('booking_date')}\n"
                                f"🕐 时间：{data.get('booking_time')}\n"
                                f"📋 类型：{data.get('consultation_type')}\n"
                                f"请登录系统查看并确认预约。",
                        is_read=False
                    )
                    await message_repo.create(teacher_msg)

                    # 发送给学生
                    student_msg = Message(
                        sender_id=teacher_id,
                        sender_name=teacher.name,
                        sender_role="teacher",
                        receiver_id=data.get("student_id"),
                        receiver_name=student_name,
                        receiver_role="student",
                        content=f"✅ 您的预约已提交成功！\n"
                                f"📅 预约日期：{data.get('booking_date')}\n"
                                f"🕐 预约时间：{data.get('booking_time')}\n"
                                f"📋 咨询类型：{data.get('consultation_type')}\n"
                                f"👨‍🏫 咨询老师：{teacher.name}\n\n"
                                f"请等待老师确认，确认后可在预约列表中查看详情。",
                        is_read=False
                    )
                    await message_repo.create(student_msg)

            # 转换为字典并处理 datetime
            result = saved.model_dump()
            if 'created_at' in result and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()
            if 'updated_at' in result and isinstance(result['updated_at'], datetime):
                result['updated_at'] = result['updated_at'].isoformat()

            return {
                "success": True,
                "message": "预约提交成功，请等待教师确认",
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"创建预约失败: {str(e)}"
            }

    async def get_student_bookings(self, student_id: str) -> list:
        bookings = await self.booking_repo.find_by_student_id(student_id)
        result = []
        for b in bookings:
            data = b.model_dump()
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result.append(data)
        return result

    async def get_all_bookings(self, skip: int = 0, limit: int = 100) -> list:
        bookings = await self.booking_repo.find_all(skip, limit)
        result = []
        for b in bookings:
            data = b.model_dump()
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result.append(data)
        return result

    async def get_pending_bookings(self) -> list:
        bookings = await self.booking_repo.find_pending()
        result = []
        for b in bookings:
            data = b.model_dump()
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result.append(data)
        return result

    async def get_today_bookings(self, date_str: str) -> list:
        bookings = await self.booking_repo.find_by_date(date_str)
        result = []
        for b in bookings:
            data = b.model_dump()
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result.append(data)
        return result

    async def confirm_booking(self, booking_id: str, teacher_id: str, teacher_name: str,
                              confirmed_date: str, confirmed_time: str, room: str) -> dict:
        try:
            await self.booking_repo.confirm_booking(
                booking_id, teacher_id, teacher_name, confirmed_date, confirmed_time, room
            )

            booking = await self.booking_repo.find_by_id(booking_id)
            if booking:
                from app.database import get_db
                from app.repositories.message_repo import MessageRepository
                db = get_db()
                message_repo = MessageRepository(db)

                # 发送确认消息给学生
                confirm_msg = Message(
                    sender_id=teacher_id,
                    sender_name=teacher_name,
                    sender_role="teacher",
                    receiver_id=booking.student_id,
                    receiver_name=booking.student_name,
                    receiver_role="student",
                    content=f"✅ 您的预约已确认！\n"
                            f"📅 确认日期：{confirmed_date}\n"
                            f"🕐 确认时间：{confirmed_time}\n"
                            f"📍 咨询室：{room}\n"
                            f"👨‍🏫 咨询老师：{teacher_name}\n\n"
                            f"请按时前往咨询室，如有问题请联系老师。",
                    is_read=False
                )
                await message_repo.create(confirm_msg)

            return {"success": True, "message": "预约已确认"}
        except Exception as e:
            return {"success": False, "message": f"确认失败: {str(e)}"}

    async def reject_booking(self, booking_id: str) -> dict:
        await self.booking_repo.update_status(booking_id, "已拒绝")
        return {"success": True, "message": "预约已拒绝"}

    async def cancel_booking(self, booking_id: str) -> dict:
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            return {"success": False, "message": "预约不存在"}
        if booking.status not in ["待确认", "已确认"]:
            return {"success": False, "message": "该预约状态不可取消"}
        await self.booking_repo.update_status(booking_id, "已取消")
        return {"success": True, "message": "预约已取消"}

    async def complete_booking(self, booking_id: str) -> dict:
        await self.booking_repo.update_status(booking_id, "已完成")
        return {"success": True, "message": "咨询已完成"}

    async def get_today_queue_count(self, date_str: str) -> int:
        return await self.booking_repo.get_today_queue_count(date_str)