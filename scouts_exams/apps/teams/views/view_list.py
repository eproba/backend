from apps.teams.models import Patrol
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render


def view_teams(request):
    if request.user.is_authenticated and request.user.scout.function >= 3:
        if not request.user.scout.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return redirect("frontpage")
        user = request.user
        teams = [user.scout.patrol.team]

        return render(
            request,
            "teams/view_team.html",
            {"teams": teams},
        )
    return redirect("frontpage")


def view_patrol(request, patrol_id):
    if request.user.is_authenticated and request.user.scout.function >= 3:
        if not request.user.scout.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return redirect("frontpage")
        patrol = get_object_or_404(Patrol, pk=patrol_id)
        scouts = patrol.scouts.filter(user__is_active=True)

        return render(
            request,
            "teams/view_patrol.html",
            {"patrol": patrol, "scouts": scouts},
        )
    return redirect("frontpage")
