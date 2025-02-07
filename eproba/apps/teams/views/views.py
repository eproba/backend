from apps.teams.models import Patrol, Team
from apps.users.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render


def manage_user(request, user_id):
    if request.user.is_authenticated and request.user.function >= 3:
        if not request.user.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return redirect("frontpage")
        user = get_object_or_404(User, id=user_id)
        enable_edit = user.function <= request.user.function
        if request.user.patrol and user.patrol:
            if request.user.patrol.team != user.patrol.team:
                enable_edit = False
        elif user.patrol:
            return render(
                request,
                "teams/manage_user.html",
                {
                    "user": user,
                    "patrols": user.patrol.team.patrol_set.all(),
                    "foreign_teams": Team.objects.all().exclude(id=user.patrol.team.id),
                    "foreign_patrols": Patrol.objects.all().exclude(
                        team_id=user.patrol.team.id
                    ),
                    "scout_ranks": User.SCOUT_RANK_CHOICES,
                    "instructor_ranks": User.INSTRUCTOR_RANK_CHOICES,
                    "functions": User.FUNCTION_CHOICES[: (request.user.function + 1)],
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
                    "scout_ranks": User.SCOUT_RANK_CHOICES,
                    "instructor_ranks": User.INSTRUCTOR_RANK_CHOICES,
                    "functions": User.FUNCTION_CHOICES[: (request.user.function + 1)],
                    "enable_edit": enable_edit,
                },
            )

        return render(
            request,
            "teams/manage_user.html",
            {
                "user": user,
                "patrols": user.patrol.team.patrol_set.all(),
                "foreign_teams": Team.objects.all().exclude(id=user.patrol.team.id),
                "foreign_patrols": Patrol.objects.all().exclude(
                    team_id=user.patrol.team.id
                ),
                "scout_ranks": User.SCOUT_RANK_CHOICES,
                "instructor_ranks": User.INSTRUCTOR_RANK_CHOICES,
                "functions": User.FUNCTION_CHOICES[: (request.user.function + 1)],
                "enable_edit": enable_edit,
            },
        )
    return redirect("frontpage")


def team_statistics(request):
    if (
        request.user.is_authenticated
        and request.user.function >= 3
        and request.user.patrol
    ):
        return render(
            request,
            "teams/team_statistics.html",
        )
    return redirect("frontpage")
