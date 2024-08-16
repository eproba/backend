import uuid

from apps.users.models import User
from django.db import models
from django.db.models import UUIDField
from django.utils import timezone

STATUS = (
    (0, "Do zrobienia"),
    (1, "Oczekuje na zatwierdzenie"),
    (2, "Zatwierdzono"),
    (3, "Odrzucono"),
)


class Worksheet(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="worksheets",
        verbose_name="Właściciel próby",
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        default=None,
        related_name="supervised_worksheets",
        blank=True,
        verbose_name="Opiekun próby",
    )
    name = models.CharField(max_length=200, verbose_name="Nazwa próby")
    is_archived = models.BooleanField(
        default=False, verbose_name="Próba zarchiwizowana?"
    )
    is_template = models.BooleanField(default=False, verbose_name="Szablon?")
    deleted = models.BooleanField(default=False, verbose_name="Usunięta?")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.rank_nickname}"

    class Meta:
        verbose_name = "Próba"
        verbose_name_plural = "Próby"


class Task(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    worksheet = models.ForeignKey(
        Worksheet, related_name="tasks", on_delete=models.CASCADE
    )
    task = models.CharField(max_length=250, verbose_name="Zadanie")
    status = models.IntegerField(choices=STATUS, default=0, verbose_name="Status")
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="approved_tasks",
        blank=True,
        verbose_name="Zatwierdzający",
    )
    approval_date = models.DateTimeField(
        default=timezone.now, blank=True, null=True, verbose_name="Data zatwierdzenia"
    )
    description = models.TextField(default="", blank=True, verbose_name="Opis zadania")

    def __str__(self):
        return str(self.task)

    class Meta:
        verbose_name = "Zadanie"
        verbose_name_plural = "Zadania"

    def save(self, *args, **kwargs):
        super(Task, self).save()
        self.worksheet.save()  # update updated_at
