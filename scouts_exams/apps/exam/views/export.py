from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from unidecode import unidecode
from weasyprint import HTML

from ..models import Exam
from .utils import prepare_for_export


def export(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "exam/exam.html",
            {"user": request.user},
        )
    user = request.user
    user_exams = [
        prepare_for_export(exam)
        for exam in Exam.objects.filter(
            scout__user=user, is_template=False, deleted=False, is_archived=False
        )
    ]
    archived_user_exams = [
        prepare_for_export(exam)
        for exam in Exam.objects.filter(
            scout__user=user, is_template=False, deleted=False, is_archived=True
        )
    ]

    patrol_exams = []
    if user.scout.function >= 2:
        patrol_exams = [
            prepare_for_export(exam)
            for exam in Exam.objects.filter(
                scout__patrol=user.scout.patrol,
                is_template=False,
                deleted=False,
                is_archived=False,
            )
        ]
    team_exams = []
    if user.scout.function >= 3:
        team_exams = [
            prepare_for_export(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team=user.scout.patrol.team,
                is_template=False,
                deleted=False,
                is_archived=False,
            )
        ]

    archived_patrol_exams = []
    if user.scout.function >= 2:
        archived_patrol_exams = [
            prepare_for_export(exam)
            for exam in Exam.objects.filter(
                scout__patrol=user.scout.patrol,
                is_template=False,
                deleted=False,
                is_archived=True,
            )
        ]

    archived_team_exams = []
    if user.scout.function >= 3:
        archived_team_exams = [
            prepare_for_export(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team=user.scout.patrol.team,
                is_template=False,
                deleted=False,
                is_archived=True,
            )
        ]

    return render(
        request,
        "exam/export.html",
        {
            "user": user,
            "user_exams": user_exams,
            "patrol_exams": patrol_exams,
            "team_exams": team_exams,
            "archived_user_exams": archived_user_exams,
            "archived_patrol_exams": archived_patrol_exams,
            "archived_team_exams": archived_team_exams,
        },
    )


def export_exam(request, hex):
    try:
        exam_user_id = int(f"0x{hex.split('0x')[1]}", 0) // 7312
        exam_id = int(f"0x{hex.split('0x')[2]}", 0) // 2137
    except Exception:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))

    exam = get_object_or_404(Exam, pk=exam_id)

    if exam.scout.user.id != exam_user_id:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))

    response = HttpResponse(
        HTML(
            string=render_to_string(
                "exam/exam_pdf.html", {"exam": exam, "should_replace_stars": True}
            )
        ).write_pdf(),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = (
        f'inline; filename="{unidecode(str(exam))} (Epróba).pdf"'
    )

    return response
