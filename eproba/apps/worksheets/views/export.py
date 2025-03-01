from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from unidecode import unidecode

try:
    from weasyprint import HTML
except OSError:
    pass

from ..models import Worksheet


def export(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "worksheets/worksheet.html",
            {"user": request.user},
        )
    user = request.user
    user_worksheets = Worksheet.objects.filter(
        user=user, deleted=False, is_archived=False
    )

    archived_user_worksheets = Worksheet.objects.filter(
        user=user, deleted=False, is_archived=True
    )

    patrol_worksheets = []
    if user.function >= 2:
        patrol_worksheets = Worksheet.objects.filter(
            user__patrol=user.patrol,
            deleted=False,
            is_archived=False,
        )

    team_worksheets = []
    if user.function >= 3:
        team_worksheets = Worksheet.objects.filter(
            user__patrol__team=user.patrol.team,
            deleted=False,
            is_archived=False,
        )

    archived_patrol_worksheets = []
    if user.function >= 2:
        archived_patrol_worksheets = Worksheet.objects.filter(
            user__patrol=user.patrol,
            deleted=False,
            is_archived=True,
        )

    archived_team_worksheets = []
    if user.function >= 3:
        archived_team_worksheets = Worksheet.objects.filter(
            user__patrol__team=user.patrol.team,
            deleted=False,
            is_archived=True,
        )

    return render(
        request,
        "worksheets/export.html",
        {
            "user": user,
            "user_worksheets": user_worksheets,
            "patrol_worksheets": patrol_worksheets,
            "team_worksheets": team_worksheets,
            "archived_user_worksheets": archived_user_worksheets,
            "archived_patrol_worksheets": archived_patrol_worksheets,
            "archived_team_worksheets": archived_team_worksheets,
        },
    )


def export_worksheet(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id)

    try:
        response = HttpResponse(
            HTML(
                string=render_to_string(
                    "worksheets/worksheet_pdf.html",
                    {"worksheet": worksheet, "should_replace_stars": True},
                )
            ).write_pdf(),
            content_type="application/pdf",
        )
    except NameError:
        messages.add_message(
            request, messages.ERROR, "Weasyprint nie jest zainstalowany."
        )
        return redirect(reverse("worksheets:worksheets"))
    response["Content-Disposition"] = (
        f'inline; filename="{unidecode(str(worksheet))} - Epróba.pdf"'
    )

    return response
