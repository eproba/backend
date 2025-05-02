import threading

from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import TeamRequestForm
from ..models import District, Team, TeamRequest


def send_team_request_email(team_request_obj):
    email = EmailMessage(
        subject=f"Zgłoszenie o dodanie drużyny: {team_request_obj.team.name}",
        body="Pojawiło się nowe zgłoszenie o dodanie drużyny. https://eproba.zhr.pl/team/requests/",
        from_email=None,
        to=["eproba@zhr.pl"],
        headers={"Reply-To": team_request_obj.created_by.email},
    )
    email.send()


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
                organization=int(request.POST.get("organization", 0)),
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

            team_request_obj = TeamRequest.objects.create(
                created_by=request.user,
                team=team,
                function_level=request.POST.get("function_level"),
            )

            send_email_thread = threading.Thread(
                target=send_team_request_email, args={team_request_obj}, daemon=True
            )
            send_email_thread.start()

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
