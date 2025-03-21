from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.tasks.tasks import (
    check_user_virtual_network_expired,
    ping_server,
    check_user_virtual_network_traffic,
)

scheduler = AsyncIOScheduler()
scheduler.add_job(
    func=ping_server,
    trigger=IntervalTrigger(minutes=4),
)

scheduler.add_job(
    func=check_user_virtual_network_expired,
    trigger=IntervalTrigger(minutes=4),
)

scheduler.add_job(
    func=check_user_virtual_network_traffic,
    trigger=IntervalTrigger(minutes=4),
)
