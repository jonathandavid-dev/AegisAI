from celery import Celery
from app.config.settings import settings

celery_app = Celery(
    "aegis_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Autodiscover background tasks registered inside app/workers/tasks.py
celery_app.autodiscover_tasks(["app.workers"])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)
