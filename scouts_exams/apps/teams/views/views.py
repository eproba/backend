from apps.teams.models import Patrol, Team
from apps.users.models import Scout, User
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render


def manage_user(request, user_id):
    if request.user.is_authenticated and request.user.scout.function >= 3:
        if not request.user.scout.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return redirect("frontpage")
        user = get_object_or_404(User, pk=user_id)
        enable_edit = user.scout.function <= request.user.scout.function
        if request.user.scout.patrol and user.scout.patrol:
            if request.user.scout.patrol.team != user.scout.patrol.team:
                enable_edit = False
        elif user.scout.patrol:
            return render(
                request,
                "teams/manage_user.html",
                {
                    "user": user,
                    "patrols": user.scout.patrol.team.patrol_set.all(),
                    "foreign_teams": Team.objects.all().exclude(
                        id=user.scout.patrol.team.id
                    ),
                    "foreign_patrols": Patrol.objects.all().exclude(
                        team_id=user.scout.patrol.team.id
                    ),
                    "scout_ranks": Scout.SCOUT_RANK_CHOICES,
                    "instructor_ranks": Scout.INSTRUCTOR_RANK_CHOICES,
                    "functions": Scout.FUNCTION_CHOICES[
                        : (request.user.scout.function + 1)
                    ],
                    "enable_edit": False,
                },
            )
        else:
            return render(
                request,
                "teams/manage_user.html",
                {
                    "user": user,
                    "patrols": Patrol.objects.all(),
                    "foreign_teams": Team.objects.all(),
                    "foreign_patrols": Patrol.objects.all(),
                    "scout_ranks": Scout.SCOUT_RANK_CHOICES,
                    "instructor_ranks": Scout.INSTRUCTOR_RANK_CHOICES,
                    "functions": Scout.FUNCTION_CHOICES[
                        : (request.user.scout.function + 1)
                    ],
                    "enable_edit": enable_edit,
                },
            )

        return render(
            request,
            "teams/manage_user.html",
            {
                "user": user,
                "patrols": user.scout.patrol.team.patrol_set.all(),
                "foreign_teams": Team.objects.all().exclude(
                    id=user.scout.patrol.team.id
                ),
                "foreign_patrols": Patrol.objects.all().exclude(
                    team_id=user.scout.patrol.team.id
                ),
                "scout_ranks": Scout.SCOUT_RANK_CHOICES,
                "instructor_ranks": Scout.INSTRUCTOR_RANK_CHOICES,
                "functions": Scout.FUNCTION_CHOICES[
                    : (request.user.scout.function + 1)
                ],
                "enable_edit": enable_edit,
            },
        )
    return redirect("frontpage")
