# Celery app must be imported so shared_task decorator uses this app
from .celery import app as celery_app

__all__ = ("celery_app",)
