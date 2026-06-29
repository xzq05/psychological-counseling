# app/repositories/booking_repo.py
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from app.models.booking import Booking
from datetime import datetime
import re


def is_valid_object_id(id_str):
    """验证是否为有效的ObjectId"""
    if not id_str:
        return False
    return bool(re.match(r'^[0-9a-fA-F]{24}$', id_str))


class BookingRepository:
    def __init__(self, db):
        self.collection: AsyncIOMotorCollection = db["bookings"]

    async def create(self, booking: Booking) -> Booking:
        data = booking.model_dump(by_alias=True, exclude={"id"})
        data = {k: v for k, v in data.items() if v is not None}
        today = datetime.now().strftime("%Y-%m-%d")
        count = await self.collection.count_documents({"booking_date": today})
        data["queue_number"] = count + 1
        result = await self.collection.insert_one(data)
        booking.id = str(result.inserted_id)
        return booking

    async def find_by_student_id(self, student_id: str):
        cursor = self.collection.find({"student_id": student_id}).sort("created_at", -1)
        bookings = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            bookings.append(Booking(**doc))
        return bookings

    async def find_by_id(self, booking_id: str):
        if not is_valid_object_id(booking_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(booking_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
            return Booking(**doc)
        return None

    async def find_all(self, skip: int = 0, limit: int = 100):
        cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
        bookings = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            bookings.append(Booking(**doc))
        return bookings

    async def find_by_date(self, date_str: str):
        cursor = self.collection.find({"booking_date": date_str}).sort("queue_number", 1)
        bookings = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            bookings.append(Booking(**doc))
        return bookings

    async def find_pending(self):
        """查询所有待确认的预约"""
        cursor = self.collection.find({"status": "待确认"}).sort("created_at", 1)
        bookings = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            bookings.append(Booking(**doc))
        return bookings

    async def update_status(self, booking_id: str, status: str):
        if not is_valid_object_id(booking_id):
            return
        await self.collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"status": status, "updated_at": datetime.now()}}
        )

    async def confirm_booking(self, booking_id: str, teacher_id: str, teacher_name: str,
                              confirmed_date: str, confirmed_time: str, room: str):
        if not is_valid_object_id(booking_id):
            return
        await self.collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {
                "status": "已确认",
                "teacher_id": teacher_id,
                "teacher_name": teacher_name,
                "confirmed_date": confirmed_date,
                "confirmed_time": confirmed_time,
                "room": room,
                "updated_at": datetime.now()
            }}
        )

    async def delete_permanently(self, booking_id: str):
        """永久删除预约"""
        if not is_valid_object_id(booking_id):
            return
        await self.collection.delete_one({"_id": ObjectId(booking_id)})

    async def delete_all(self):
        """删除所有预约"""
        await self.collection.delete_many({})

    async def get_today_queue_count(self, date_str: str) -> int:
        return await self.collection.count_documents({"booking_date": date_str})