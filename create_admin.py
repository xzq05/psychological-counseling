import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime


async def create_admin():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["psychological_counseling"]
    collection = db["users"]

    # 删除旧的 admin
    await collection.delete_many({"username": "admin"})

    # 加密密码: 123456
    password = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    admin = {
        "username": "admin",
        "password": password,
        "name": "系统管理员",
        "phone": "13800000000",
        "role": "admin",
        "status": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = await collection.insert_one(admin)
    print(f"✅ 管理员账号创建成功！ID: {result.inserted_id}")
    print("📧 账号: admin")
    print("🔑 密码: 123456")

    client.close()


if __name__ == "__main__":
    asyncio.run(create_admin())