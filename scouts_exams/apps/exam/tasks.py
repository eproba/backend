import logging
from time import time

logger = logging.getLogger(__name__)


def remove_expired_deleted_exams():
    from .models import Exam

    count = 0

    for exam in Exam.objects.filter(deleted=True):
        if exam.updated_at.timestamp() + 2592000 < time():
            exam.delete()
            count += 1

    logger.info(f"Removed {count} expired deleted exams.")
