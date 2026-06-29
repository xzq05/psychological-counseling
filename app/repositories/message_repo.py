# app/repositories/message_repo.py
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from app.models.message import Message, Announcement
from datetime import datetime
import re


def is_valid_object_id(id_str):
    if not id_str:
        return False
    return bool(re.match(r'^[0-9a-fA-F]{24}$', id_str))


class MessageRepository:
    def __init__(self, db):
        self.collection: AsyncIOMotorCollection = db["messages"]

    async def create(self, message: Message) -> Message:
        data = message.model_dump(by_alias=True, exclude={"id"})
        # 确保 datetime 字段正确
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at']
        result = await self.collection.insert_one(data)
        message.id = str(result.inserted_id)
        return message

    async def find_by_users(self, user1_id: str, user2_id: str, limit: int = 50):
        cursor = self.collection.find({
            "$or": [
                {"sender_id": user1_id, "receiver_id": user2_id},
                {"sender_id": user2_id, "receiver_id": user1_id}
            ]
        }).sort("created_at", -1).limit(limit)

        messages = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            # 转换 datetime
            if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                doc['created_at'] = doc['created_at'].isoformat()
            messages.append(Message(**doc))
        return list(reversed(messages))

    async def find_unread_count(self, receiver_id: str) -> int:
        return await self.collection.count_documents({
            "receiver_id": receiver_id,
            "is_read": False
        })

    async def mark_all_read(self, receiver_id: str, sender_id: str):
        await self.collection.update_many(
            {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "is_read": False
            },
            {"$set": {"is_read": True, "read_at": datetime.now()}}
        )

    async def get_chat_users(self, user_id: str):
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"sender_id": user_id},
                        {"receiver_id": user_id}
                    ]
                }
            },
            {
                "$group": {
                    "_id": None,
                    "users": {
                        "$addToSet": {
                            "$cond": [
                                {"$eq": ["$sender_id", user_id]},
                                "$receiver_id",
                                "$sender_id"
                            ]
                        }
                    }
                }
            }
        ]
        result = await self.collection.aggregate(pipeline).to_list(None)
        if result and result[0].get("users"):
            return [u for u in result[0]["users"] if u != user_id]
        return []


class AnnouncementRepository:
    def __init__(self, db):
        self.collection: AsyncIOMotorCollection = db["announcements"]

    async def create(self, announcement: Announcement) -> Announcement:
        data = announcement.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(data)
        announcement.id = str(result.inserted_id)
        return announcement

    async def find_all_active(self):
        cursor = self.collection.find({"is_active": True}).sort("priority", -1).sort("created_at", -1)
        announcements = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                doc['created_at'] = doc['created_at'].isoformat()
            if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                doc['updated_at'] = doc['updated_at'].isoformat()
            announcements.append(Announcement(**doc))
        return announcements

    async def find_all(self):
        cursor = self.collection.find().sort("created_at", -1)
        announcements = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                doc['created_at'] = doc['created_at'].isoformat()
            if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                doc['updated_at'] = doc['updated_at'].isoformat()
            announcements.append(Announcement(**doc))
        return announcements

    async def delete(self, announcement_id: str):
        if not is_valid_object_id(announcement_id):
            return
        await self.collection.delete_one({"_id": ObjectId(announcement_id)})