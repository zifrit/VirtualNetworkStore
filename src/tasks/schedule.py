from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.tasks.tasks import check_user_virtual_network_expired

scheduler = AsyncIOScheduler()
scheduler.add_job(
    func=check_user_virtual_network_expired,
    trigger=IntervalTrigger(seconds=10),
)
