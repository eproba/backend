import datetime

from django.contrib import messages
from django.forms.formsets import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from unidecode import unidecode
from weasyprint import HTML

from ..teams.models import Patrol
from .forms import ExamCreateForm, ExtendedExamCreateForm, SubmitTaskForm, TaskForm
from .models import Exam, Task


def prepare_exam(exam):
    _all = 0
    _done = 0
    exam.show_submit_task_button = False
    exam.show_sent_tasks_button = False
    exam.show_description_column = False
    for task in exam.tasks.all():
        _all += 1
        if task.status == 2:
            _done += 1
        elif task.status == 0 or task.status == 3:
            exam.show_submit_task_button = True
        elif task.status == 1:
            exam.show_sent_tasks_button = True
        if task.description is not "":
            exam.show_description_column = True
    if _all != 0:
        percent = int(round(_done / _all, 2) * 100)
        exam.percent = f"{str(percent)}%"
    else:
        exam.percent = "Nie masz jeszcze dodanych żadnych zadań"
    exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id * 7312)}{hex(exam.id * 2137)}"

    return exam


def view_exams(request):
    if request.user.is_authenticated:
        user = request.user
        exams = []
        for exam in Exam.objects.filter(scout__user=user):
            exams.append(prepare_exam(exam))
        return render(
            request,
            "exam/exam.html",
            {"user": user, "exams_list": exams},
        )
    else:
        return render(
            request,
            "exam/exam.html",
            {"user": request.user, "exams_list": []},
        )


def print_exam(request, hex):
    try:
        exam_user_nickname = bytearray.fromhex(hex.split("0x")[0]).decode()
        exam_user_id = int(int(f"0x{hex.split('0x')[1]}", 0) / 7312)
        exam_id = int(int(f"0x{hex.split('0x')[2]}", 0) / 2137)
    except:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))
    exams = []
    for exam in Exam.objects.filter(id=exam_id):
        if (
            unidecode(exam.scout.user.nickname) != exam_user_nickname
            or exam.scout.user.id != exam_user_id
        ):
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
    response[
        "Content-Disposition"
    ] = f'inline; filename="{unidecode(str(exam))} (by epróba).pdf"'

    return response


def view_shared_exams(request, hex):
    user = request.user
    try:
        exam_user_nickname = bytearray.fromhex(hex.split("0x")[0]).decode()
        exam_user_id = int(int(f"0x{hex.split('0x')[1]}", 0) / 7312)
        exam_id = int(int(f"0x{hex.split('0x')[2]}", 0) / 2137)
    except:
        messages.add_message(
            request, messages.INFO, "Podany link do próby jest nieprawidłowy."
        )
        return redirect(reverse("frontpage"))
    exams = []
    for exam in Exam.objects.filter(id=exam_id):
        if (
            unidecode(exam.scout.user.nickname) != exam_user_nickname
            or exam.scout.user.id != exam_user_id
        ):
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
    user = request.user
    exams = []
    if request.user.scout.function == 0 or request.user.scout.function == 1:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji prób."
        )
        return redirect(reverse("exam:exam"))
    elif request.user.scout.function == 2:
        for exam in Exam.objects.filter(scout__team__id=user.scout.team.id).exclude(
            scout=user.scout
        ):
            exams.append(prepare_exam(exam))
    elif request.user.scout.function == 3 or request.user.scout.function == 4:
        for exam in Exam.objects.filter(scout__team__id=user.scout.team.id):
            exams.append(prepare_exam(exam))
    elif request.user.scout.function >= 5:
        for exam in Exam.objects.filter(scout__team__id=user.scout.team.id):
            exams.append(prepare_exam(exam))
    patrols = Patrol.objects.filter(team__id=user.scout.team.id)
    return render(
        request,
        "exam/manage_exams.html",
        {"user": user, "exams_list": exams, "patrols": patrols},
    )


def create_exam(request):
    TaskFormSet = formset_factory(TaskForm, extra=1)
    if request.method == "POST":
        if request.user.scout.function >= 2:
            exam = ExtendedExamCreateForm(request.user, request.POST)
        else:
            exam = ExamCreateForm(request.POST)
        tasks = TaskFormSet(request.POST, initial=[{"task": " "}])
        if exam.is_valid():
            if request.user.scout.function >= 2:
                exam_obj = exam.save()
            else:
                exam_obj = exam.save(commit=False)
                exam_obj.scout = request.user.scout
                exam_obj.save()
            if tasks.is_valid():
                tasks_data = tasks.cleaned_data
                for task in tasks_data:
                    if "task" in task:
                        Task.objects.create(exam=exam_obj, task=task["task"])

            messages.add_message(request, messages.INFO, "Próba została utworzona.")
            if request.GET.get("next", False):
                return redirect(request.GET.get("next"))
            else:
                return redirect(reverse("exam:exam"))

    else:
        if request.user.scout.function >= 2:
            exam = ExtendedExamCreateForm(request.user)
        else:
            exam = ExamCreateForm()
        tasks = TaskFormSet()

    return render(request, "exam/create_exam.html", {"exam": exam, "tasks": tasks})


def check_tasks(request):
    if not request.user.is_authenticated:
        return render(request, "exam/check_tasks.html")
    user = request.user
    exams = []
    if user.scout.function >= 2:
        for exam in Exam.objects.all():
            tasks = []
            for task in exam.tasks.filter(status=1, approver=user.scout):
                tasks.append(task)
            if tasks != []:
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
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if request.user.scout != exam.scout or task.status != 1 or task.exam != exam:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji tego zadania."
        )
        return redirect(reverse("exam:exam"))
    Task.objects.filter(task=task).update(status=0, approver=None)
    return redirect(f"/exam/{str(exam_id)}/tasks/sent")


def refuse_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1 or task.exam != exam or task.approver != request.user.scout:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("exam:check_tasks"))
    Task.objects.filter(id=task.id).update(status=3, approver=None)
    return redirect(reverse("exam:check_tasks"))


def accept_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1 or task.exam != exam or task.approver != request.user.scout:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do akceptacji tego zadania."
        )
        return redirect(reverse("exam:check_tasks"))
    Task.objects.filter(id=task.id).update(status=2, approval_date=timezone.now())
    return redirect(reverse("exam:check_tasks"))


def force_refuse_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        if task.exam != exam or request.user.scout.function < 2:
            return HttpResponse("401 Unauthorized", status=401)
        Task.objects.filter(id=task.id).update(
            status=3, approver=None, approval_date=None
        )
        return HttpResponse("OK", status=200)
    else:
        if task.exam != exam or request.user.scout.function < 2:
            messages.add_message(
                request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
            )
            return redirect(reverse("exam:edit_exams"))
        Task.objects.filter(id=task.id).update(
            status=3, approver=None, approval_date=None
        )
        return redirect(reverse("exam:edit_exams"))


def force_accept_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        if task.exam != exam or request.user.scout.function < 2:
            return HttpResponse("401 Unauthorized", status=401)
        Task.objects.filter(id=task.id).update(
            status=2,
            approver=request.user.scout,
            approval_date=timezone.now(),
        )
        return HttpResponse("OK", status=200)
    else:
        if task.exam != exam or request.user.scout.function < 2:
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
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user.scout != exam.scout:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("exam:exam"))
    if request.method == "POST":
        submit_task_form = SubmitTaskForm(
            request,
            request.user,
            exam,
            request.POST,
            instance=Task.objects.get(id=request.POST.__getitem__("task")),
        )
        if submit_task_form.is_valid():
            submited_task = submit_task_form.save(commit=False)
            submited_task.user = request.user
            submited_task.exam = exam
            submited_task.approval_date = timezone.now()
            submited_task.status = 1
            submited_task.save()

            return redirect(reverse("exam:exam"))

    else:
        submit_task_form = SubmitTaskForm(request=request, user=request.user, exam=exam)
    return render(
        request,
        "exam/request_task_check.html",
        {
            "user": request.user,
            "exam": exam,
            "forms": [submit_task_form],
        },
    )
