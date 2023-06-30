__version__ = "2023.06.30"

from .celery import app as celery_app

__all__ = ("celery_app",)
