from apps.teams.models import Patrol
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render


def view_team(request):
    if request.user.is_authenticated and request.user.function >= 3:
        if not request.user.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return redirect("frontpage")

        if request.GET.get("graph"):
            return render(
                request,
                "teams/view_team_graph.html",
            )

        return render(
            request,
            "teams/view_team.html",
            {"team": request.user.patrol.team},
        )
    return redirect("frontpage")


def view_patrol(request, patrol_id):
    if request.user.is_authenticated and request.user.function >= 3:
        if not request.user.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return redirect("frontpage")
        patrol = get_object_or_404(Patrol, id=patrol_id)
        users = patrol.users.filter(is_active=True).order_by("nickname")

        return render(
            request,
            "teams/view_patrol.html",
            {"patrol": patrol, "users": users},
        )
    return redirect("frontpage")
