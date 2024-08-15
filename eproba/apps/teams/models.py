import uuid

from django.db import models
from django.db.models import UUIDField


class District(models.Model):
    """
    Okręg
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Okręg"
        verbose_name_plural = "Okręgi"

    def __str__(self):
        return str(self.name)


class Team(models.Model):
    """
    Drużyna
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10)
    district = models.ForeignKey(
        District, on_delete=models.RESTRICT, null=True, blank=True
    )

    class Meta:
        verbose_name = "Drużyna"
        verbose_name_plural = "Drużyny"

    def __str__(self):
        return str(self.name)


class Patrol(models.Model):
    """
    Zastęp
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, null=True, blank=True)

    class Meta:
        verbose_name = "Zastęp"
        verbose_name_plural = "Zastępy"

    def __str__(self):
        if self.team:
            return f"{self.team.short_name} - {self.name}"
        return f"{self.name} (brak drużyny)"
