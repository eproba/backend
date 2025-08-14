import os
import uuid

from apps.teams.models import OrganizationChoice, Team
from apps.users.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UUIDField
from django.utils import timezone

STATUS = (
    (0, "Do zrobienia"),
    (1, "Oczekuje na zatwierdzenie"),
    (2, "Zatwierdzono"),
    (3, "Odrzucono"),
)

TASK_CATEGORY = (
    ("general", "Ogólne"),
    ("individual", "Indywidualne"),
)


def template_image_upload_path(instance, filename):
    """Generate upload path for template images."""
    ext = filename.split(".")[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join("template_images", filename)


def validate_template_image(file):
    """Validate the uploaded template image."""
    valid_extensions = ["jpg", "jpeg", "png", "svg", "gif"]
    ext = file.name.split(".")[-1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension: {ext}")
    if file.size > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError("File size exceeds the limit of 5MB.")


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
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data utworzenia próby"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Data ostatniej aktualizacji próby"
    )
    notes = models.TextField(
        default="",
        blank=True,
        verbose_name="Notatki do próby, ukryte przed użytkownikami",
    )
    template = models.ForeignKey(
        "TemplateWorksheet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="worksheets",
        verbose_name="Szablon próby",
    )

    final_challenge = models.CharField(
        max_length=250,
        default="",
        blank=True,
        verbose_name="Próba końcowa (bieg)",
    )
    final_challenge_description = models.TextField(
        default="",
        blank=True,
        verbose_name="Opis próby końcowej (biegu)",
    )

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
    notes = models.TextField(
        default="",
        blank=True,
        verbose_name="Notatki do zadania, ukryte przed użytkownikami",
    )
    category = models.CharField(
        max_length=20,
        choices=TASK_CATEGORY,
        default="general",
        verbose_name="Kategoria",
    )
    order = models.IntegerField(
        default=0, verbose_name="Kolejność zadania w próbie/kategorii"
    )

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
    image = models.FileField(
        upload_to=template_image_upload_path,
        validators=[validate_template_image],
        blank=True,
        null=True,
        verbose_name="Obrazek szablonu",
        help_text="Obsługiwane formaty: JPG, PNG, SVG oraz GIF. Maksymalny rozmiar: 5MB",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(
        default=0,
        verbose_name="Priorytet szablonu",
        help_text="Szablony o wyższym priorytecie będą wyświetlane wyżej na liście.",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Szablon"
        verbose_name_plural = "Szablony"


class TemplateTaskGroup(models.Model):
    """Defines a group of template tasks where user must pick a constrained number."""

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        TemplateWorksheet,
        related_name="task_groups",
        on_delete=models.CASCADE,
        verbose_name="Szablon",
    )
    name = models.CharField(
        max_length=120,
        verbose_name="Nazwa grupy",
        help_text="Wyświetlana nazwa grupy zadań",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Opis",
        help_text="Instrukcja / kontekst dla użytkownika",
    )
    min_tasks = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Minimalny wybór",
        help_text="Minimalna liczba zadań do wybrania (puste = brak)",
    )
    max_tasks = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Maksymalny wybór",
        help_text="Maksymalna liczba zadań (puste = brak limitu)",
    )

    class Meta:
        verbose_name = "Grupa zadań szablonu"
        verbose_name_plural = "Grupy zadań szablonu"

    def __str__(self):
        return f"{self.name} ({self.template.name})"

    def clean(self):
        if (
            self.min_tasks is not None
            and self.max_tasks is not None
            and self.min_tasks > self.max_tasks
        ):
            raise ValidationError(
                "Minimalna liczba nie może być większa niż maksymalna."
            )


class TemplateTask(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        TemplateWorksheet, related_name="tasks", on_delete=models.CASCADE
    )
    task = models.CharField(max_length=250, blank=True, verbose_name="Zadanie szablonu")
    description = models.TextField(
        blank=True, default="", verbose_name="Opis zadania szablonu"
    )
    template_notes = models.TextField(
        blank=True, default="", verbose_name="Notatki do zadania szablonu"
    )
    group = models.ForeignKey(
        TemplateTaskGroup,
        related_name="tasks",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Grupa zadań szablonu",
        help_text="Opcjonalna grupa z ograniczeniami wyboru",
    )
    category = models.CharField(
        max_length=20,
        choices=TASK_CATEGORY,
        default="general",
        verbose_name="Kategoria",
    )
    order = models.IntegerField(
        default=0, verbose_name="Kolejność zadania w szablonie/kategorii"
    )

    def __str__(self):
        return self.task

    class Meta:
        verbose_name = "Zadanie szablonu"
        verbose_name_plural = "Zadania szablonu"

    def clean(self):
        if self.group and self.group.template != self.template:
            raise ValidationError(
                "Zadanie musi należeć do tego samego szablonu co grupa zadań."
            )
