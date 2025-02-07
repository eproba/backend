from django.contrib import messages
from django.shortcuts import redirect, render


def team_requests(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Nie masz uprawnień do przeglądania tej strony.")
        return redirect("frontpage")
    return render(request, "teams/team_requests.html")
