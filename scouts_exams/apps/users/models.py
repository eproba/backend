from apps.teams.models import Patrol, Team
from apps.users.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.dispatch import receiver
from django.utils import timezone


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email address", unique=True)
    nickname = models.CharField(max_length=20)
    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=40, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.nickname})"

    def full_name(self):
        return (
            f"{self.first_name} {self.last_name}"
            if self.first_name is not None and self.last_name is not None
            else self.first_name
            if self.first_name is not None
            else self.last_name
            if self.last_name is not None
            else None
        )

    def full_name_nickname(self):
        return (
            f"{self.first_name} {self.last_name} „{self.nickname}”"
            if self.first_name is not None
            and self.last_name is not None
            and self.nickname is not None
            else f"{self.first_name} {self.last_name}"
            if self.first_name is not None and self.last_name is not None
            else self.first_name
            if self.first_name is not None
            else self.last_name
            if self.last_name is not None
            else self.nickname
            if self.nickname is not None
            else None
        )


class Scout(models.Model):
    RANK_CHOICES = [
        (" ", "bez stopnia"),
        ("mł.", "mł."),
        ("wyw.", "wyw."),
        ("ćwik", "ćwik"),
        ("HO", "HO"),
        ("pwd. HO", "pwd. HO"),
        ("HR", "HR"),
        ("pwd. HR", "pwd. HR"),
        ("phm. HR", "phm. HR"),
        ("hm. HR", "hm. HR"),
    ]
    FUNCTION_CHOICES = [
        (0, "Druh"),
        (1, "Podzastępowy"),
        (2, "Zastępowy"),
        (3, "Przyboczny"),
        (4, "Drużynowy"),
        (5, "Wyższa funkcja"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    patrol = models.ForeignKey(
        Patrol,
        on_delete=models.RESTRICT,
        null=True,
        default=None,
        related_name="scouts",
    )
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default=" ")
    function = models.IntegerField(choices=FUNCTION_CHOICES, default=0)

    REQUIRED_FIELDS = ["initials", "patrol", "rank"]

    def __str__(self):
        return f"{self.rank} {self.user.nickname}"

    def team_short_name(self):
        return self.patrol.team.short_name if self.patrol is not None else None


@receiver(models.signals.post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
    if created:
        Scout.objects.create(user=instance)
    instance.scout.save()
