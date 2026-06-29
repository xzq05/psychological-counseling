# app/api/__init__.py
from .auth import router as auth_router
from .bookings import router as bookings_router
from .admin import router as admin_router
from .schedules import router as schedules_router
from .messages import router as messages_router  # 添加这行