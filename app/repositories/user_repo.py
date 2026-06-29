# app/repositories/user_repo.py
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from app.models.user import User
from datetime import datetime, timedelta
import re


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


def is_valid_object_id(id_str):
    if not id_str:
        return False
    return bool(re.match(r'^[0-9a-fA-F]{24}$', id_str))


class UserRepository:
    def __init__(self, db):
        self.collection: AsyncIOMotorCollection = db["users"]

    async def find_by_username(self, username: str):
        doc = await self.collection.find_one({"username": username})
        if doc:
            doc["_id"] = str(doc["_id"])
            return User(**doc)
        return None

    async def find_by_reset_token(self, token: str):
        doc = await self.collection.find_one({"reset_token": token})
        if doc:
            doc["_id"] = str(doc["_id"])
            return User(**doc)
        return None

    async def find_by_id(self, user_id: str):
        if not is_valid_object_id(user_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
            return User(**doc)
        return None

    async def find_by_role(self, role: str):
        cursor = self.collection.find({"role": role, "status": "active"})
        users = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(User(**doc))
        return users

    async def find_teachers_pending(self):
        cursor = self.collection.find({
            "role": "teacher",
            "$or": [
                {"teacher_verified": False},
                {"teacher_verified": {"$exists": False}}
            ],
            "status": "active"
        })
        users = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "teacher_verified" not in doc:
                doc["teacher_verified"] = False
            users.append(User(**doc))
        return users

    async def find_all_students(self):
        cursor = self.collection.find({"role": "student"})
        users = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(User(**doc))
        return users

    async def find_all_teachers(self):
        cursor = self.collection.find({"role": "teacher"})
        users = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(User(**doc))
        return users

    async def find_all(self):
        cursor = self.collection.find({"status": "active"})
        users = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(User(**doc))
        return users

    async def create(self, user: User):
        data = user.model_dump(by_alias=True, exclude={"id"})
        data = {k: v for k, v in data.items() if v is not None}
        if 'created_at' not in data or not data['created_at']:
            data['created_at'] = get_beijing_time()
        result = await self.collection.insert_one(data)
        user.id = str(result.inserted_id)
        return user

    async def update(self, user_id: str, data: dict):
        if not is_valid_object_id(user_id):
            return
        data["updated_at"] = get_beijing_time()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data}
        )

    async def delete(self, user_id: str):
        if not is_valid_object_id(user_id):
            return
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": "inactive", "updated_at": get_beijing_time()}}
        )

    async def delete_permanently(self, user_id: str):
        if not is_valid_object_id(user_id):
            return
        await self.collection.delete_one({"_id": ObjectId(user_id)})

    async def verify_teacher(self, user_id: str):
        if not is_valid_object_id(user_id):
            return
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "teacher_verified": True,
                "status": "active",
                "updated_at": get_beijing_time()
            }}
        )

    async def count_by_role(self, role: str) -> int:
        return await self.collection.count_documents({"role": role, "status": "active"})