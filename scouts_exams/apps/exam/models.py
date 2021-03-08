import datetime

from django.db import models
from django.utils import timezone

from ..users.models import Scout, User


class Exam(models.Model):
    scout = models.ForeignKey(
        Scout,
        on_delete=models.RESTRICT,
        null=True,
        default=None,
        related_name="scout",
        blank=True,
    )
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} - {self.scout}"

    class Meta:
        verbose_name = "Próba"
        verbose_name_plural = "Próby"


class Task(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    task = models.CharField(max_length=250)
    is_done = models.BooleanField(default=False)
    is_await = models.BooleanField(default=False)
    approver = models.ForeignKey(
        Scout,
        on_delete=models.RESTRICT,
        null=True,
        default=None,
        related_name="approver",
        blank=True,
    )
    approval_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.task

    REQUIRED_FIELDS = ["exam", "task"]

    class Meta:
        verbose_name = "Zadanie"
        verbose_name_plural = "Zadania"


class SentTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, default=None)
    sent_date = models.DateTimeField("Data wysłania prośby", default=timezone.now)

    def __str__(self):
        return f"{self.task} - sent by {self.user}"
