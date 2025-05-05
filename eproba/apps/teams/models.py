import uuid

from django.db import models


class OrganizationChoice(models.IntegerChoices):
    """
    Czy drużyna należy do organizacji harcerek czy harcerzy
    """

    MALE = 0, "Organizacja Harcerzy"
    FEMALE = 1, "Organizacja Harcerek"


class District(models.Model):
    """
    Okręg
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Okręg"
        verbose_name_plural = "Okręgi"

    def __str__(self):
        return self.name


class Team(models.Model):
    """
    Drużyna
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=20)
    district = models.ForeignKey(
        District, on_delete=models.RESTRICT, related_name="teams"
    )
    is_verified = models.BooleanField(default=False)
    organization = models.IntegerField(
        choices=OrganizationChoice.choices, default=OrganizationChoice.choices[0][0]
    )

    class Meta:
        verbose_name = "Drużyna"
        verbose_name_plural = "Drużyny"

    def __str__(self):
        return self.name

    def get_registration_link(self):
        return f"https://eproba.zhr.pl/signup/?team={self.id}"


class Patrol(models.Model):
    """
    Zastęp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="patrols")

    class Meta:
        verbose_name = "Zastęp"
        verbose_name_plural = "Zastępy"

    def __str__(self):
        return f"{self.team.short_name} - {self.name}" if self.team else self.name

    def get_registration_link(self):
        return f"https://eproba.zhr.pl/signup/?patrol={self.id}"


class TeamRequest(models.Model):
    """
    Zgłoszenie drużyny
    """

    STATUS_CHOICES = [
        ("submitted", "Zgłoszone"),
        ("approved", "Zaakceptowane"),
        ("rejected", "Odrzucone"),
        ("pending_verification", "Oczekuje na dodatkową weryfikację"),
    ]

    FUNCTION_CHOICES = [
        (3, "Przyboczny"),
        (4, "Drużynowy"),
        (5, "Wyższa funkcja"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="team_requests"
    )
    accepted_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="accepted_team_requests",
        null=True,
        blank=True,
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="submitted"
    )
    function_level = models.IntegerField(choices=FUNCTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Zgłoszenie drużyny"
        verbose_name_plural = "Zgłoszenia drużyn"

    def __str__(self):
        return f"{self.team.name} - {self.get_status_display()}"
