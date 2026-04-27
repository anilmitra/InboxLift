from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "inboxlift",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.warmup_tasks",
        "app.tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    beat_schedule={
        # Run warming cycle every 30 minutes during business hours
        "run-warmup-cycle": {
            "task": "app.tasks.warmup_tasks.run_warmup_cycle",
            "schedule": crontab(minute="*/30"),
        },
        # Check inboxes every hour
        "check-email-delivery": {
            "task": "app.tasks.warmup_tasks.check_email_delivery",
            "schedule": crontab(minute="15", hour="*/1"),
        },
        # Update analytics snapshots daily
        "update-daily-analytics": {
            "task": "app.tasks.maintenance_tasks.update_all_analytics",
            "schedule": crontab(minute="0", hour="2"),  # 2am UTC
        },
        # Reset daily counters at midnight
        "reset-daily-counters": {
            "task": "app.tasks.maintenance_tasks.reset_daily_counters",
            "schedule": crontab(minute="0", hour="0"),
        },
    },
)
