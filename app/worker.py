"""Celery worker configuration and tasks."""

from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "openmotiv",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.missions", "app.tasks.robots"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Fair scheduling
    worker_concurrency=4,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "check-robot-health-every-minute": {
            "task": "app.tasks.robots.check_fleet_health",
            "schedule": 60.0,  # Every 60 seconds
        },
        "process-scheduled-missions-every-30s": {
            "task": "app.tasks.missions.process_scheduled_missions",
            "schedule": 30.0,
        },
    },
)
