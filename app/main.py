# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection
from app.utils.redis_client import close_redis_client
from app.api import auth_router, bookings_router, admin_router, schedules_router, messages_router
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时连接数据库
    await connect_to_mongo()
    print("=" * 50)
    print("✅ MongoDB 连接成功")
    print("✅ 心理咨询预约系统启动成功")
    print("=" * 50)
    yield
    # 关闭时清理连接
    await close_mongo_connection()
    await close_redis_client()
    print("✅ 连接已关闭")


app = FastAPI(
    title="心理咨询预约系统",
    version="1.0.0",
    lifespan=lifespan
)

# 确保 static 目录存在
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    os.makedirs(os.path.join(static_dir, "css"))
    os.makedirs(os.path.join(static_dir, "js"))

app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(auth_router)
app.include_router(bookings_router)
app.include_router(admin_router)
app.include_router(schedules_router)
app.include_router(messages_router)  # 添加这行


# ===== 健康检查端点 =====
@app.get("/health")
async def health_check():
    """健康检查 - 用于云平台监控"""
    return {
        "status": "healthy",
        "service": "心理咨询预约系统",
        "version": "1.0.0"
    }


@app.get("/api/health/db")
async def db_health_check():
    """数据库健康检查"""
    from app.database import get_db
    try:
        db = get_db()
        await db.command('ping')
        return {"status": "healthy", "database": "MongoDB"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}