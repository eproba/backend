import uuid

from apps.teams.models import OrganizationChoice, Team
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
    description = models.TextField(blank=True, default="", verbose_name="Opis próby")
    is_archived = models.BooleanField(
        default=False, verbose_name="Próba zarchiwizowana?"
    )
    deleted = models.BooleanField(default=False, verbose_name="Usunięta?")
    created_at = models.DateTimeField(auto_now_add=True)
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


class TemplateWorksheet(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team, related_name="templates", on_delete=models.CASCADE, null=True, blank=True
    )
    organization = models.IntegerField(
        choices=OrganizationChoice.choices, null=True, blank=True
    )
    name = models.CharField(max_length=200, verbose_name="Nazwa szablonu")
    description = models.TextField(blank=True, default="", verbose_name="Opis szablonu")
    template_notes = models.TextField(
        blank=True, default="", verbose_name="Notatki do szablonu"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Szablon"
        verbose_name_plural = "Szablony"


class TemplateTask(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        TemplateWorksheet, related_name="tasks", on_delete=models.CASCADE
    )
    task = models.CharField(max_length=250, verbose_name="Zadanie szablonu")
    description = models.TextField(
        blank=True, default="", verbose_name="Opis zadania szablonu"
    )
    template_notes = models.TextField(
        blank=True, default="", verbose_name="Notatki do zadania szablonu"
    )

    def __str__(self):
        return self.task

    class Meta:
        verbose_name = "Zadanie szablonu"
        verbose_name_plural = "Zadania szablonu"
