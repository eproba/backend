import json
import uuid

from apps.teams.models import Patrol
from apps.users.utils import UUIDEncoder
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.db.models import UUIDField


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [(0, "Mężczyzna"), (1, "Kobieta"), (2, "Inna")]
    SCOUT_RANK_CHOICES = [
        (0, "brak stopnia"),
        (1, '"biszkopt"'),
        (2, "mł./och."),
        (3, "wyw./trop."),
        (4, "ćwik/sam."),
        (5, "HO/węd."),
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
        (1, "Podzastępowy(-a)"),
        (2, "Zastępowy(-a)"),
        (3, "Przyboczny(-a)"),
        (4, "Drużynowy(-a)"),
        (5, "Wyższa funkcja"),
    ]

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("email address", unique=True)
    nickname = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=40, blank=True, null=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, null=True, blank=True)

    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

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

    objects = UserManager()

    class Meta:
        verbose_name = "Użytkownik"
        verbose_name_plural = "Użytkownicy"

    def __str__(self):
        return f"{self.email} ({self.nickname})"

    def get_short_name(self):
        return self.full_name() or self.email.split("@")[0]

    def get_nickname(self):
        return self.nickname or self.full_name() or self.email.split("@")[0]

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
        rank = (
            f"{self.get_instructor_rank_display()} "
            if self.instructor_rank != 0
            else ""
        )

        _gender = (
            self.patrol.team.organization if self.patrol is not None else self.gender
        )

        scout_rank_male = {
            1: "biszkopt",
            2: "mł.",
            3: "wyw.",
            4: "ćwik",
            5: "HO",
            6: "HR",
        }

        scout_rank_female = {
            1: "biszkopt",
            2: "och.",
            3: "trop.",
            4: "sam.",
            5: "węd.",
            6: "HR",
        }

        if _gender == 0:
            scout_rank = scout_rank_male.get(self.scout_rank, "")
        elif _gender == 1:
            scout_rank = scout_rank_female.get(self.scout_rank, "")
        else:
            scout_rank = self.get_scout_rank_display()

        return f"{rank}{scout_rank}"

    def full_rank(self):

        _gender = (
            self.patrol.team.organization if self.patrol is not None else self.gender
        )

        instructor_rank_male = {1: "przewodnik", 2: "podharcmistrz", 3: "harcmistrz"}

        instructor_rank_female = {
            1: "przewodniczka",
            2: "podharcmistrzyni",
            3: "harcmistrzyni",
        }

        scout_rank_male = {
            1: "biszkopt",
            2: "młodzik",
            3: "wywiadowca",
            4: "ćwik",
            5: "harcerz orli",
            6: "harcerz Rzeczypospolitej",
        }

        scout_rank_female = {
            1: "biszkopt",
            2: "ochotniczka",
            3: "tropicielka",
            4: "samarytanka",
            5: "wędrowniczka",
            6: "harcerka Rzeczypospolitej",
        }

        if _gender == 0:
            instructor_rank = instructor_rank_male.get(self.instructor_rank, "")
            scout_rank = scout_rank_male.get(self.scout_rank, "")
        elif _gender == 1:
            instructor_rank = instructor_rank_female.get(self.instructor_rank, "")
            scout_rank = scout_rank_female.get(self.scout_rank, "")
        else:
            instructor_rank = (
                self.get_instructor_rank_display() if self.instructor_rank != 0 else ""
            )
            scout_rank = self.get_scout_rank_display() if self.scout_rank != 0 else ""

        if instructor_rank:
            instructor_rank = f"{instructor_rank} "

        return f"{instructor_rank}{scout_rank}"

    @property
    def rank_nickname(self):
        return f"{self.rank()} {self.get_nickname()}"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email_verified": self.email_verified,
            "is_staff": self.is_staff,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "patrol": self.patrol.id if self.patrol is not None else None,
            "scout_rank": self.scout_rank,
            "instructor_rank": self.instructor_rank,
            "function": self.function,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), cls=UUIDEncoder)
