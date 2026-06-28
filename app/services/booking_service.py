# app/services/booking_service.py
from app.models.booking import Booking
from app.repositories.booking_repo import BookingRepository


class BookingService:
    def __init__(self, booking_repo: BookingRepository):
        self.booking_repo = booking_repo

    async def create_booking(self, data: dict) -> dict:
        """学生创建预约"""
        booking = Booking(**data)
        saved = await self.booking_repo.create(booking)
        return {
            "success": True,
            "message": "预约提交成功，请等待教师确认",
            "data": saved.model_dump()
        }

    async def get_student_bookings(self, student_id: str) -> list:
        """学生查看自己的预约"""
        bookings = await self.booking_repo.find_by_student_id(student_id)
        return [b.model_dump() for b in bookings]

    async def get_all_bookings(self, skip: int = 0, limit: int = 100) -> list:
        """获取所有预约"""
        bookings = await self.booking_repo.find_all(skip, limit)
        return [b.model_dump() for b in bookings]

    async def get_pending_bookings(self) -> list:
        """获取所有待确认预约（教师用）"""
        bookings = await self.booking_repo.find_pending()
        return [b.model_dump() for b in bookings]

    async def get_today_bookings(self, date_str: str) -> list:
        """获取某天所有预约"""
        bookings = await self.booking_repo.find_by_date(date_str)
        return [b.model_dump() for b in bookings]

    async def confirm_booking(self, booking_id: str, teacher_id: str, teacher_name: str,
                              confirmed_date: str, confirmed_time: str, room: str) -> dict:
        """教师确认预约"""
        await self.booking_repo.confirm_booking(
            booking_id, teacher_id, teacher_name, confirmed_date, confirmed_time, room
        )
        return {"success": True, "message": "预约已确认"}

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