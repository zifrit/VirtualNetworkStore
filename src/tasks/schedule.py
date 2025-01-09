CELERY_BEAT_SCHEDULE = {
    "add-every-30-seconds": {
        "task": "src.tasks.tasks.task_check_user_virtual_network_expired",  # Путь к задаче
        "schedule": 10,  # Каждые 30 секунд
    },
}
