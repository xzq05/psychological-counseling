# app/services/schedule_service.py
from app.models.schedule import Schedule
from app.repositories.schedule_repo import ScheduleRepository
from app.utils.redis_client import get_redis_client


class ScheduleService:
    def __init__(self, schedule_repo: ScheduleRepository):
        self.schedule_repo = schedule_repo
        self.redis = None

    async def _get_redis(self):
        if not self.redis:
            self.redis = await get_redis_client()
        return self.redis

    async def get_schedule_with_cache(self, counselor_id: str, target_date: str) -> dict:
        cache_key = f"schedule:counselor:{counselor_id}:{target_date}"
        redis_client = await self._get_redis()

        cached_data = await redis_client.hgetall(cache_key)
        if cached_data:
            slots = []
            for start_time, status in cached_data.items():
                slots.append({
                    "start_time": start_time.decode(),
                    "status": status.decode()
                })
            return {
                "counselor_id": counselor_id,
                "date": target_date,
                "time_slots": slots,
                "from_cache": True
            }

        schedule = await self.schedule_repo.find_by_counselor_and_date(
            counselor_id, target_date
        )

        if schedule:
            for slot in schedule.time_slots:
                await redis_client.hset(cache_key, slot.start_time, slot.status)
            await redis_client.expire(cache_key, 3600)
            return schedule.model_dump()

        return None

    async def create_schedule(self, schedule_data: dict) -> dict:
        schedule = Schedule(**schedule_data)
        saved = await self.schedule_repo.create(schedule)

        redis_client = await self._get_redis()
        cache_key = f"schedule:counselor:{saved.counselor_id}:{saved.date}"
        await redis_client.delete(cache_key)

        return saved.model_dump()