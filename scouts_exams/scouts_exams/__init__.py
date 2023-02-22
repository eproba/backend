__version__ = "2023.02.22"

from .celery import app as celery_app

__all__ = ("celery_app",)
