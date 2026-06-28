# app/api/schedules.py
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.schedule_repo import ScheduleRepository
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/api/schedules", tags=["排班"])


def get_schedule_service():
    db = get_db()
    schedule_repo = ScheduleRepository(db)
    return ScheduleService(schedule_repo)


@router.get("")
async def get_schedule(
    counselor_id: str = Query(..., description="咨询师ID"),
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    service: ScheduleService = Depends(get_schedule_service)
):
    """查询咨询师某日排班"""
    result = await service.get_schedule_with_cache(counselor_id, date)
    if not result:
        return {
            "counselor_id": counselor_id,
            "date": date,
            "time_slots": [],
            "message": "暂无排班"
        }
    return result


@router.post("")
async def create_schedule(
    schedule_data: dict,
    service: ScheduleService = Depends(get_schedule_service)
):
    """创建排班"""
    return await service.create_schedule(schedule_data)