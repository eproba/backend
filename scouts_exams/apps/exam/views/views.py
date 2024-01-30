from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from fcm_django.models import FCMDevice
from firebase_admin.messaging import (
    Message,
    WebpushConfig,
    WebpushFCMOptions,
    WebpushNotification,
)
from unidecode import unidecode
from weasyprint import HTML

from ...teams.models import Patrol
from ..forms import SubmitTaskForm
from ..models import Exam, Task
from .utils import prepare_exam


def view_exams(request):
    if request.user.is_authenticated:
        user = request.user
        exams = [
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                scout__user=user, is_template=False, deleted=False, is_archived=False
            )
        ]

        return render(
            request,
            "exam/exam.html",
            {"user": user, "exams_list": exams},
        )
    return render(
        request,
        "exam/exam.html",
        {"user": request.user, "exams_list": []},
    )


def print_exam(request, hex):
    try:
        exam_user_id = int(f"0x{hex.split('0x')[1]}", 0) // 7312
        exam_id = int(f"0x{hex.split('0x')[2]}", 0) // 2137
    except Exception:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))
    exams = []
    for exam in Exam.objects.filter(id=exam_id, deleted=False):
        if exam.scout.user.id != exam_user_id:
            messages.add_message(
                request, messages.INFO, "Podany link do próby jest nieprawidłowy."
            )
            return redirect(reverse("frontpage"))

    if exams is []:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))

    exam = get_object_or_404(Exam, pk=exam_id)
    response = HttpResponse(
        HTML(string=render_to_string("exam/exam_pdf.html", {"exam": exam})).write_pdf(),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = (
        f'inline; filename="{unidecode(str(exam))} (by epróba).pdf"'
    )

    return response


def view_shared_exams(request, hex):
    user = request.user
    try:
        exam_user_id = int(f"0x{hex.split('0x')[1]}", 0) // 7312
        exam_id = int(f"0x{hex.split('0x')[2]}", 0) // 2137
    except Exception:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))
    exams = []
    for exam in Exam.objects.filter(id=exam_id, deleted=False):
        if exam.scout.user.id != exam_user_id:
            messages.add_message(
                request, messages.INFO, "Podany link do próby jest nieprawidłowy."
            )
            return redirect(reverse("frontpage"))

        exams.append(prepare_exam(exam))

    if exams is []:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))

    return render(
        request,
        "exam/exam.html",
        {"user": user, "exams_list": exams, "is_shared": True},
    )


def manage_exams(request):
    if not request.user.is_authenticated:
        return render(request, "exam/manage_exams.html")
    if not request.user.scout.patrol:
        messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
        return render(request, "exam/manage_exams.html")
    user = request.user
    exams = []
    if request.user.scout.function < 2:
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
                is_archived=False,
                is_template=False,
                deleted=False,
            ).exclude(scout=user.scout)
        )

    elif request.user.scout.function in [3, 4]:
        exams.extend(
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                is_archived=False,
                is_template=False,
                deleted=False,
            )
        )

    elif request.user.scout.function >= 5:
        exams.extend(
            prepare_exam(exam)
            for exam in Exam.objects.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                is_archived=False,
                is_template=False,
                deleted=False,
            )
        )

    exams.extend(
        prepare_exam(exam)
        for exam in Exam.objects.filter(
            supervisor__user_id=user.id,
            is_archived=False,
            is_template=False,
            deleted=False,
        )
    )

    exams.sort(key=lambda x: x.updated_at, reverse=True)
    patrols = Patrol.objects.filter(team__id=user.scout.patrol.team.id).order_by("name")
    return render(
        request,
        "exam/manage_exams.html",
        {"user": user, "exams_list": exams, "patrols": patrols},
    )


def check_tasks(request):
    if not request.user.is_authenticated:
        return render(request, "exam/check_tasks.html")
    user = request.user
    exams = []
    if user.scout.function >= 2:
        for exam in Exam.objects.filter(deleted=False, is_archived=False):
            if tasks := list(exam.tasks.filter(status=1, approver=user.scout)):
                exam.task_list = tasks
                exams.append(exam)
        return render(
            request,
            "exam/check_tasks.html",
            {"user": user, "exams_list": exams},
        )
    messages.add_message(
        request, messages.INFO, "Nie masz uprawnień do akceptacji zadań."
    )
    return redirect(reverse("exam:exam"))


def sent_tasks(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user.scout != exam.scout:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("exam:exam"))
    return render(
        request,
        "exam/sent_tasks.html",
        {
            "user": request.user,
            "exam": exam,
            "tasks_list": Task.objects.filter(status=1, exam=exam),
        },
    )


def unsubmit_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if request.user.scout != exam.scout or task.status != 1 or task.exam != exam:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji tego zadania."
        )
        return redirect(reverse("exam:exam"))
    Task.objects.filter(task=task).update(status=0, approver=None)
    return redirect(f"/exam/{str(exam_id)}/tasks/sent")


def reject_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1 or task.exam != exam or task.approver != request.user.scout:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("exam:check_tasks"))
    Task.objects.filter(id=task.id).update(status=3)
    exam.save()  # update exam's last modification date
    return redirect(reverse("exam:check_tasks"))


def accept_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1 or task.exam != exam or task.approver != request.user.scout:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do akceptacji tego zadania."
        )
        return redirect(reverse("exam:check_tasks"))
    Task.objects.filter(id=task.id).update(status=2, approval_date=timezone.now())
    exam.save()  # update exam's last modification date
    return redirect(reverse("exam:check_tasks"))


def force_reject_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        if (
            task.exam != exam
            or request.user.scout.function < 2
            or request.user.scout.function < exam.scout.function
        ):
            return HttpResponse("401 Unauthorized", status=401)
        Task.objects.filter(id=task.id).update(status=3, approver=request.user.scout)
        exam.save()  # update exam's last modification date
        return HttpResponse("OK", status=200)
    if (
        task.exam != exam
        or request.user.scout.function < 2
        or request.user.scout.function < exam.scout.function
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("exam:edit_exams"))
    Task.objects.filter(id=task.id).update(status=3, approver=None)
    return redirect(reverse("exam:edit_exams"))


def force_accept_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        if (
            task.exam != exam
            or request.user.scout.function < 2
            or request.user.scout.function < exam.scout.function
        ):
            return HttpResponse("401 Unauthorized", status=401)
        Task.objects.filter(id=task.id).update(
            status=2,
            approver=request.user.scout,
            approval_date=timezone.now(),
        )
        exam.save()  # update exam's last modification date
        return HttpResponse("OK", status=200)
    if (
        task.exam != exam
        or request.user.scout.function < 2
        or request.user.scout.function < exam.scout.function
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do zaliczenia tego zadania."
        )
        return redirect(reverse("exam:edit_exams"))
    Task.objects.filter(id=task.id).update(
        status=2,
        approver=request.user.scout,
        approval_date=timezone.now(),
    )
    return redirect(reverse("exam:edit_exams"))


def submit_task(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, deleted=False)
    if request.user.scout != exam.scout:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("exam:exam"))
    if request.method == "POST":
        submit_task_form = SubmitTaskForm(
            request,
            exam,
            request.POST,
            instance=Task.objects.get(id=request.POST.__getitem__("task")),
        )
        if submit_task_form.is_valid():
            submitted_task = submit_task_form.save(commit=False)
            submitted_task.user = request.user
            submitted_task.exam = exam
            submitted_task.approval_date = timezone.now()
            submitted_task.status = 1
            submitted_task.save()

            FCMDevice.objects.filter(user=submitted_task.approver.user).send_message(
                Message(
                    webpush=WebpushConfig(
                        notification=WebpushNotification(
                            title="Nowe zadanie do sprawdzenia",
                            body=f"Pojawił się nowy punkt do sprawdzenia dla {submitted_task.user.scout}.",
                        ),
                        fcm_options=WebpushFCMOptions(
                            link="https://"
                            + request.get_host()
                            + reverse("exam:check_tasks")
                        ),
                    ),
                )
            )
            messages.success(
                request, "Prośba o zaakceptowanie zadania została wysłana."
            )
            return redirect(reverse("exam:exam"))

    else:
        submit_task_form = SubmitTaskForm(request=request, exam=exam)
    return render(
        request,
        "exam/request_task_check.html",
        {
            "user": request.user,
            "exam": exam,
            "forms": [submit_task_form],
        },
    )
