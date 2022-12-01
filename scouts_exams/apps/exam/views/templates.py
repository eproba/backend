from django.shortcuts import render

from ..models import Exam
from .utils import prepare_exam


def templates(request):
    exams = []
    if request.user.is_authenticated:
        exams.extend(
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                is_template=True,
                scout__patrol__team=request.user.scout.patrol.team,
                deleted=False,
            )
        )

    return render(
        request, "exam/templates.html", {"user": request.user, "exams_list": exams}
    )
