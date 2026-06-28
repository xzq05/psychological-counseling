# app/repositories/schedule_repo.py
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from app.models.schedule import Schedule
from datetime import datetime


class ScheduleRepository:
    def __init__(self, db):
        self.collection: AsyncIOMotorCollection = db["schedules"]

    async def find_by_counselor_and_date(self, counselor_id: str, target_date: str):
        doc = await self.collection.find_one({
            "counselor_id": counselor_id,
            "date": target_date
        })
        return Schedule(**doc) if doc else None

    async def create(self, schedule: Schedule):
        data = schedule.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(data)
        schedule.id = str(result.inserted_id)
        return schedule

    async def update_time_slot(self, schedule_id: str, start_time: str, status: str, booking_id: str = None):
        update_data = {"time_slots.$.status": status}
        if booking_id:
            update_data["time_slots.$.booking_id"] = booking_id
        await self.collection.update_one(
            {
                "_id": ObjectId(schedule_id),
                "time_slots.start_time": start_time
            },
            {"$set": update_data}
        )