__version__ = "2024.01.30"

from .celery import app as celery_app

__all__ = ("celery_app",)
