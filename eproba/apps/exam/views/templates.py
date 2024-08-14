from django.contrib import messages
from django.shortcuts import render

from ..models import Exam
from .utils import prepare_exam, prepare_for_export


def templates(request):
    exams = []
    if request.user.is_authenticated:
        if not request.user.scout.patrol:
            messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
            return render(request, "exam/templates.html")
        exams.extend(
            prepare_for_export(exam)
            for exam in Exam.objects.filter(
                is_template=True,
                scout__patrol__team=request.user.scout.patrol.team,
                deleted=False,
            )
        )

    return render(
        request, "exam/templates.html", {"user": request.user, "exams_list": exams}
    )
