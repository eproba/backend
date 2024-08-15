from django.contrib import messages
from django.shortcuts import render

from ..models import Worksheet


def templates(request):
    worksheets = []
    if request.user.is_authenticated:
        if not request.user.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return render(request, "worksheets/templates.html")
        worksheets = Worksheet.objects.filter(
            is_template=True,
            user__patrol__team=request.user.patrol.team,
            deleted=False,
        )

    return render(
        request,
        "worksheets/templates.html",
        {"user": request.user, "worksheets_list": worksheets},
    )
