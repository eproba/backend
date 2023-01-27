from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from ...teams.models import Patrol
from ..models import Exam
from .utils import prepare_exam


def archive(request):
    if not request.user.is_authenticated:
        return render(request, "exam/archive.html")
    if not request.user.scout.patrol:
        messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
        return render(request, "exam/archive.html")
    user = request.user
    exams = []
    if request.user.scout.function in [0, 1]:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji prób."
        )
        return redirect(reverse("exam:exam"))
    if request.user.scout.function == 2:
        exams.extend(
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                scout__function__lt=user.scout.function,
                is_archived=True,
                deleted=False,
            ).exclude(scout=user.scout)
        )

    elif request.user.scout.function in [3, 4]:
        exams.extend(
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                is_archived=True,
                deleted=False,
            )
        )

    elif request.user.scout.function >= 5:
        exams.extend(
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                is_archived=True,
                deleted=False,
            )
        )

    exams.extend(
        prepare_exam(exam)
        for exam in Exam.objects.filter(
            supervisor__user_id=user.id, is_archived=True, deleted=False
        )
    )

    patrols = Patrol.objects.filter(team__id=user.scout.patrol.team.id).order_by("name")
    return render(
        request,
        "exam/archive.html",
        {"user": user, "exams_list": exams, "patrols": patrols},
    )
