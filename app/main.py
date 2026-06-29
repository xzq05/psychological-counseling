# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection
from app.utils.redis_client import close_redis_client
from app.api import auth_router, bookings_router, admin_router, schedules_router, messages_router, posts_router
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    print("=" * 50)
    print("✅ MongoDB 连接成功")
    print("✅ 心理咨询预约系统启动成功")
    print("=" * 50)
    yield
    await close_mongo_connection()
    await close_redis_client()
    print("✅ 连接已关闭")


app = FastAPI(
    title="心理咨询预约系统",
    version="1.0.0",
    lifespan=lifespan
)

# 设置模板
templates = Jinja2Templates(directory="templates")

# 确保 static 目录存在
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    os.makedirs(os.path.join(static_dir, "css"))
    os.makedirs(os.path.join(static_dir, "js"))

app.mount("/static", StaticFiles(directory="static"), name="static")

# ===== 注册API路由 =====
app.include_router(auth_router)
app.include_router(bookings_router)
app.include_router(admin_router)
app.include_router(schedules_router)
app.include_router(messages_router)
app.include_router(posts_router)

# ===== 页面路由 =====
@app.get("/post_detail")
async def post_detail_page(request: Request, id: str):
    """帖子详情页面"""
    return templates.TemplateResponse("post_detail.html", {"request": request, "post_id": id})


@app.get("/post_edit")
async def post_edit_page(request: Request, id: str):
    """帖子编辑页面"""
    return templates.TemplateResponse("post_edit.html", {"request": request, "post_id": id})


@app.get("/posts")
async def posts_list_page(request: Request):
    """全部帖子列表页面"""
    return templates.TemplateResponse("posts_list.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查"""
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