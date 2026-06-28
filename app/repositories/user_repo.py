# app/repositories/user_repo.py
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from app.models.user import User
from datetime import datetime


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
        """查找待审核的教师账号"""
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
        """查找所有学生"""
        cursor = self.collection.find({"role": "student"})
        users = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(User(**doc))
        return users

    async def find_all_teachers(self):
        """查找所有教师（包括待审核的）"""
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
        result = await self.collection.insert_one(data)
        user.id = str(result.inserted_id)
        return user

    async def update(self, user_id: str, data: dict):
        data["updated_at"] = datetime.now()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data}
        )

    async def delete(self, user_id: str):
        """软删除（禁用）"""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": "inactive", "updated_at": datetime.now()}}
        )

    async def delete_permanently(self, user_id: str):
        """永久删除用户"""
        await self.collection.delete_one({"_id": ObjectId(user_id)})

    async def verify_teacher(self, user_id: str):
        """审核通过教师账号"""
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "teacher_verified": True,
                "status": "active",
                "updated_at": datetime.now()
            }}
        )

    async def count_by_role(self, role: str) -> int:
        return await self.collection.count_documents({"role": role, "status": "active"})