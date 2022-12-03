import logging
from time import time

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def remove_expired_deleted_exams():
    from .models import Exam

    count = 0

    for exam in Exam.objects.filter(deleted=True):
        if exam.modification_date.timestamp() + 2592000 < time():
            exam.delete()
            count += 1

    logger.info(f"Removed {count} expired deleted exams.")
