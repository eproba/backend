__version__ = "2022.12.01.1"

from .celery import app as celery_app

__all__ = ("celery_app",)
