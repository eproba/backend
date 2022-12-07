from django.db import models
from django.utils import timezone

from ..users.models import Scout

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
        related_name="scout",
        verbose_name="Właściciel próby",
    )
    supervisor = models.ForeignKey(
        Scout,
        on_delete=models.RESTRICT,
        null=True,
        default=None,
        related_name="supervisor",
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
        return f"{self.name} - {self.scout}"

    class Meta:
        verbose_name = "Próba"
        verbose_name_plural = "Próby"


class Task(models.Model):
    exam = models.ForeignKey(Exam, related_name="tasks", on_delete=models.CASCADE)
    task = models.CharField(max_length=250, verbose_name="Zadanie")
    status = models.IntegerField(choices=STATUS, default=0, verbose_name="Status")
    approver = models.ForeignKey(
        Scout,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="approver",
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
        self.exam.save()  # update updated_at
