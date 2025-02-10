from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import TeamRequestForm
from ..models import District, Team, TeamRequest


def team_request(request):
    if not request.user.is_authenticated:
        return render(request, "teams/team_request_unauthorized.html")

    if request.method == "POST":
        form = TeamRequestForm(request.POST)
        if form.is_valid():

            patrols = [
                name.strip()
                for name in request.POST.getlist("patrols[]", [])
                if name.strip()
            ]

            if not patrols:
                messages.error(request, "Dodaj przynajmniej jeden zastęp.")
                return render(
                    request,
                    "teams/team_request.html",
                    {"form": form, "districts": District.objects.all()},
                )

            team = Team.objects.create(
                name=request.POST.get("team_name"),
                short_name=request.POST.get("team_short_name"),
                district=District.objects.get(id=request.POST.get("district")),
                is_verified=False,
            )

            for patrol_name in patrols:
                team.patrols.create(name=patrol_name)

            request.user.patrol = (
                team.patrols.filter(name=request.POST.get("user_patrol")).first()
                or team.patrols.first()
            )
            request.user.function = 0

            request.user.save()

            TeamRequest.objects.create(
                created_by=request.user,
                team=team,
                function_level=request.POST.get("function_level"),
            )

            return redirect(reverse("teams:team_request_success"))

    else:
        form = TeamRequestForm()

    return render(
        request,
        "teams/team_request.html",
        {"form": form},
    )


def team_request_success(request):
    return render(request, "teams/team_request_success.html")
