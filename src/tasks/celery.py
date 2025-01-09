from celery import Celery
from src.core.settings import redis_settings
from src.tasks.schedule import CELERY_BEAT_SCHEDULE

celery_app = Celery(
    "tasks",
    broker=f"redis://{redis_settings.host}:{redis_settings.port}/0",
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,  # Повтор подключения при неудаче
    broker_connection_retry=True,  # Повтор подключения в случае временной потери соединения
    broker_connection_max_retries=5,  # Количество попыток подключения
    broker_connection_retry_delay=2.0,  # Интервал между попытками (в секундах)
    timezone="UTC",  # Часовой пояс
    enable_utc=True,  # Включить поддержку UTC
)


# celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
