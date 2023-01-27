__version__ = "2023.01.27"

from .celery import app as celery_app

__all__ = ("celery_app",)
