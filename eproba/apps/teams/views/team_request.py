from apps.teams.models import District, Patrol, Team
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse


def team_request(request):
    if not request.user.is_authenticated:
        return render(request, "teams/team_request_unauthorized.html")

    if request.method == "POST":
        district_id = request.POST.get("district")
        team_name = request.POST.get("team_name")
        team_short_name = request.POST.get("team_short_name")
        patrols = request.POST.getlist("patrols[]")
        user_patrol = request.POST.get("user_patrol")
        print(request.POST)

        if not all([district_id, team_name, team_short_name, patrols]):
            messages.error(request, "Wypełnij wszystkie wymagane pola.")
            print(district_id, team_name, team_short_name, patrols)
            return render(
                request,
                "teams/team_request.html",
                {"districts": District.objects.all()},
            )

        district = get_object_or_404(District, id=district_id)
        patrols = [patrol.strip() for patrol in patrols if patrol.strip()]

        if not patrols:
            messages.error(request, "Dodaj przynajmniej jeden zastęp.")
            return render(
                request,
                "teams/team_request.html",
                {"districts": District.objects.all()},
            )

        team = Team.objects.create(
            name=team_name,
            short_name=team_short_name,
            district=district,
            is_verified=False,
        )

        for patrol in patrols:
            team.patrol_set.create(name=patrol)

        team.save()
        try:
            request.user.patrol = team.patrol_set.get(name=user_patrol or patrols[0])
        except Patrol.DoesNotExist:
            request.user.patrol = None
            messages.error(request, "Nie udało się przypisać użytkownika do zastępu.")
        request.user.save()

        return redirect(reverse("teams:team_request_success"))

    return render(
        request, "teams/team_request.html", {"districts": District.objects.all()}
    )


def team_request_success(request):
    return render(request, "teams/team_request_success.html")
