from apps.teams.models import Patrol, Team
from apps.users.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.dispatch import receiver
from django.utils import timezone


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email address", unique=True)
    nickname = models.CharField(max_length=20)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.nickname})"


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
    team = models.ForeignKey(
        Team, on_delete=models.RESTRICT, null=True, default=None, related_name="scouts"
    )
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default=" ")
    function = models.IntegerField(choices=FUNCTION_CHOICES, default=0)

    REQUIRED_FIELDS = ["initials", "patrol", "team", "rank"]

    def __str__(self):
        return f"{self.rank} {self.user.nickname}"


@receiver(models.signals.post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
    if created:
        Scout.objects.create(user=instance)
    instance.scout.save()
