from django.db import models
from django.utils import timezone

from ..users.models import Scout, User

STATUS = (
    (0, "Do zrobienia"),
    (1, "Oczekuje na zatwierdzenie"),
    (2, "Zatwierdzono"),
    (3, "Odrzucono"),
)


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
    exam = models.ForeignKey(Exam, related_name="tasks", on_delete=models.CASCADE)
    task = models.CharField(max_length=250)
    status = models.IntegerField(choices=STATUS, default=0)
    approver = models.ForeignKey(
        Scout,
        on_delete=models.RESTRICT,
        null=True,
        default=None,
        related_name="approver",
        blank=True,
    )
    approval_date = models.DateTimeField(default=timezone.now, null=True)

    def __str__(self):
        return self.task

    REQUIRED_FIELDS = ["exam", "task"]

    class Meta:
        verbose_name = "Zadanie"
        verbose_name_plural = "Zadania"


# TODO: merge SentTask model with Task
class SentTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, default=None)
    sent_date = models.DateTimeField("Data wysłania prośby", default=timezone.now)

    def __str__(self):
        return f"{self.task} - sent by {self.user}"
