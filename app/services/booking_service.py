# app/services/booking_service.py
from app.models.booking import Booking
from app.repositories.booking_repo import BookingRepository
from datetime import datetime


class BookingService:
    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    def _serialize_booking(self, booking) -> dict:
        """将 Booking 对象转换为 JSON 可序列化的字典"""
        data = booking.model_dump()
        # 处理 datetime 对象
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        return data

    async def create_booking(self, data: dict) -> dict:
        """学生创建预约"""
        try:
            booking = Booking(**data)
            saved = await self.booking_repo.create(booking)

            result = self._serialize_booking(saved)

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
        """学生查看自己的预约"""
        bookings = await self.booking_repo.find_by_student_id(student_id)
        result = []
        for b in bookings:
            result.append(self._serialize_booking(b))
        return result

    async def get_all_bookings(self, skip: int = 0, limit: int = 100) -> list:
        """获取所有预约"""
        bookings = await self.booking_repo.find_all(skip, limit)
        result = []
        for b in bookings:
            result.append(self._serialize_booking(b))
        return result

    async def get_pending_bookings(self) -> list:
        """获取所有待确认预约（教师用）"""
        bookings = await self.booking_repo.find_pending()
        result = []
        for b in bookings:
            result.append(self._serialize_booking(b))
        return result

    async def get_today_bookings(self, date_str: str) -> list:
        """获取某天所有预约"""
        bookings = await self.booking_repo.find_by_date(date_str)
        result = []
        for b in bookings:
            result.append(self._serialize_booking(b))
        return result

    async def confirm_booking(self, booking_id: str, teacher_id: str, teacher_name: str,
                              confirmed_date: str, confirmed_time: str, room: str) -> dict:
        """教师确认预约"""
        try:
            await self.booking_repo.confirm_booking(
                booking_id, teacher_id, teacher_name, confirmed_date, confirmed_time, room
            )
            return {"success": True, "message": "预约已确认"}
        except Exception as e:
            return {"success": False, "message": f"确认失败: {str(e)}"}

    async def reject_booking(self, booking_id: str) -> dict:
        """教师拒绝预约"""
        await self.booking_repo.update_status(booking_id, "已拒绝")
        return {"success": True, "message": "预约已拒绝"}

    async def cancel_booking(self, booking_id: str) -> dict:
        """学生取消预约"""
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            return {"success": False, "message": "预约不存在"}
        if booking.status not in ["待确认", "已确认"]:
            return {"success": False, "message": "该预约状态不可取消"}
        await self.booking_repo.update_status(booking_id, "已取消")
        return {"success": True, "message": "预约已取消"}

    async def complete_booking(self, booking_id: str) -> dict:
        """完成咨询"""
        await self.booking_repo.update_status(booking_id, "已完成")
        return {"success": True, "message": "咨询已完成"}

    async def get_today_queue_count(self, date_str: str) -> int:
        return await self.booking_repo.get_today_queue_count(date_str)