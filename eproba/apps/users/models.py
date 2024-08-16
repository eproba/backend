import json
import uuid

from apps.teams.models import Patrol
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.db.models import UUIDField
from django.utils import timezone
from users.utils import UUIDEncoder


class User(AbstractBaseUser, PermissionsMixin):
    SCOUT_RANK_CHOICES = [
        (0, "brak stopnia"),
        (1, '"biszkopt"'),
        (2, "mł."),
        (3, "wyw."),
        (4, "ćwik"),
        (5, "HO"),
        (6, "HR"),
    ]
    INSTRUCTOR_RANK_CHOICES = [
        (0, "brak stopnia"),
        (1, "pwd."),
        (2, "phm."),
        (3, "hm."),
    ]
    FUNCTION_CHOICES = [
        (0, "Druh"),
        (1, "Podzastępowy"),
        (2, "Zastępowy"),
        (3, "Przyboczny"),
        (4, "Drużynowy"),
        (5, "Wyższa funkcja"),
    ]

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("email address", unique=True)
    nickname = models.CharField(max_length=20)
    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=40, blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    patrol = models.ForeignKey(
        Patrol,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="users",
    )
    scout_rank = models.IntegerField(choices=SCOUT_RANK_CHOICES, default=0)
    instructor_rank = models.IntegerField(choices=INSTRUCTOR_RANK_CHOICES, default=0)
    function = models.IntegerField(choices=FUNCTION_CHOICES, default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "patrol", "scout_rank", "instructor_rank"]

    objects = UserManager()

    class Meta:
        verbose_name = "Użytkownik"
        verbose_name_plural = "Użytkownicy"

    def __str__(self):
        return f"{self.email} ({self.nickname})"

    def full_name(self):
        return (
            f"{self.first_name} {self.last_name}"
            if self.first_name is not None and self.last_name is not None
            else (
                self.first_name
                if self.first_name is not None
                else self.last_name if self.last_name is not None else None
            )
        )

    def full_name_nickname(self):
        return (
            f"{self.first_name} {self.last_name} „{self.nickname}”"
            if self.first_name is not None
            and self.last_name is not None
            and self.nickname is not None
            else (
                f"{self.first_name} {self.last_name}"
                if self.first_name is not None and self.last_name is not None
                else (
                    self.first_name
                    if self.first_name is not None
                    else (
                        self.last_name
                        if self.last_name is not None
                        else self.nickname if self.nickname is not None else None
                    )
                )
            )
        )

    def team_short_name(self):
        return self.patrol.team.short_name if self.patrol is not None else None

    def rank(self):
        return (
            f"{self.get_instructor_rank_display()} {self.get_scout_rank_display()}"
            if self.instructor_rank != 0
            else self.get_scout_rank_display()
        )

    @property
    def rank_nickname(self):
        return f"{self.rank()} {self.nickname}"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_staff": self.is_staff,
            "is_active": self.is_active,
            "date_joined": self.date_joined,
            "patrol": self.patrol.id if self.patrol is not None else None,
            "scout_rank": self.scout_rank,
            "instructor_rank": self.instructor_rank,
            "function": self.function,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), cls=UUIDEncoder)
