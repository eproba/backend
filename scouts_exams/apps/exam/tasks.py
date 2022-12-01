from time import time

from celery import shared_task


@shared_task
def remove_expired_deleted_exams():
    from .models import Exam

    for exam in Exam.objects.filter(deleted=True):
        if exam.modification_date.timestamp() + 2592000 < time():
            exam.delete()
