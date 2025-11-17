"""
Celery Application Configuration

Configures Celery for asynchronous task processing.
"""

from celery import Celery

from job_pricing.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "job_pricing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "src.job_pricing.tasks.*": {"queue": "job_pricing"},
    },
    # Result expiration
    result_expires=3600,  # 1 hour
    # Task execution limits
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.job_pricing.tasks"])
