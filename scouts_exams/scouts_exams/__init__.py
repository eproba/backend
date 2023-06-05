__version__ = "2023.06.05"

from .celery import app as celery_app

__all__ = ("celery_app",)
