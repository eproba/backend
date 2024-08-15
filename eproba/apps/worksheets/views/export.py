from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import Worksheet

# from weasyprint import HTML


def export(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "worksheets/worksheet.html",
            {"user": request.user},
        )
    user = request.user
    user_worksheets = Worksheet.objects.filter(
        user=user, is_template=False, deleted=False, is_archived=False
    )

    archived_user_worksheets = Worksheet.objects.filter(
        user=user, is_template=False, deleted=False, is_archived=True
    )

    patrol_worksheets = []
    if user.function >= 2:
        patrol_worksheets = Worksheet.objects.filter(
            patrol=user.patrol,
            is_template=False,
            deleted=False,
            is_archived=False,
        )

    team_worksheets = []
    if user.function >= 3:
        team_worksheets = Worksheet.objects.filter(
            patrol__team=user.patrol.team,
            is_template=False,
            deleted=False,
            is_archived=False,
        )

    archived_patrol_worksheets = []
    if user.function >= 2:
        archived_patrol_worksheets = Worksheet.objects.filter(
            patrol=user.patrol,
            is_template=False,
            deleted=False,
            is_archived=True,
        )

    archived_team_worksheets = []
    if user.function >= 3:
        archived_team_worksheets = Worksheet.objects.filter(
            patrol__team=user.patrol.team,
            is_template=False,
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


def export_worksheet(request, hex):
    try:
        worksheet_user_id = int(f"0x{hex.split('0x')[1]}", 0) // 7312
        worksheet_id = int(f"0x{hex.split('0x')[2]}", 0) // 2137
    except Exception:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))

    worksheet = get_object_or_404(Worksheet, id=worksheet_id)

    if worksheet.user.id != worksheet_user_id:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))

    # response = HttpResponse(
    #     HTML(
    #         string=render_to_string(
    #             "worksheets/worksheet_pdf.html", {"worksheet": worksheet, "should_replace_stars": True}
    #         )
    #     ).write_pdf(),
    #     content_type="application/pdf",
    # )
    # response["Content-Disposition"] = (
    #     f'inline; filename="{unidecode(str(worksheets))} (Epróba).pdf"'
    # )
    #
    # return response
    return HttpResponse("Not implemented", status=501)
