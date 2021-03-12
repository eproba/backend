import datetime

from django import forms
from django.contrib import messages
from django.db.models import CharField, Q, Value
from django.forms import Select
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from unidecode import unidecode

from ..teams.models import Patrol
from ..users.models import Scout, User
from .models import Exam, SentTask, Task


def view_exams(request):
    user = request.user
    exams = []
    for exam in Exam.objects.filter(scout__user=user):
        _all = 0
        _done = 0
        for task in exam.task_set.all():
            _all += 1
            if task.is_done:
                _done += 1
        if _all != 0:
            percent = int(round(_done / _all, 2) * 100)
            exam.percent = f"{str(percent)}%"
        else:
            exam.percent = "Nie masz jeszcze żadnych zadań"
        exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id*7312)}{hex(exam.id*2137)}"
        exams.append(exam)
    return render(
        request,
        "exam/exam.html",
        {"user": user, "exams_list": exams},
    )


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

        _all = 0
        _done = 0
        for task in exam.task_set.all():
            _all += 1
            if task.is_done:
                _done += 1
        if _all != 0:
            percent = int(round(_done / _all, 2) * 100)
            exam.percent = f"{str(percent)}%"
        else:
            exam.percent = "Ta próba nie ma jeszcze dodanych żadnych zadań"
        exams.append(exam)
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


def edit_exams(request):
    user = request.user
    exams = []
    if (
        not request.user.scout.is_team_leader
        and not request.user.scout.is_patrol_leader
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji prób."
        )
        return redirect(reverse("exam:exam"))
    for exam in Exam.objects.filter(scout__team=user.scout.team).exclude(
        scout=user.scout
    ):
        _all = 0
        _done = 0
        for task in exam.task_set.all():
            _all += 1
            if task.is_done:
                _done += 1
        if _all != 0:
            percent = int(round(_done / _all, 2) * 100)
            exam.percent = f"{str(percent)}%"
        else:
            exam.percent = "Ta próba nie ma jeszcze dodanych żadnych zadań"
        exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id*7312)}{hex(exam.id*2137)}"
        exams.append(exam)
    return render(
        request,
        "exam/edit_exams.html",
        {"user": user, "exams_list": exams},
    )


def check_tasks(request):
    user = request.user
    exams = []
    if (
        not request.user.scout.is_team_leader
        and not request.user.scout.is_patrol_leader
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do akceptacji zadań."
        )
        return redirect(reverse("exam:exam"))
    for exam in Exam.objects.all():
        tasks = []
        for task in exam.task_set.filter(is_await=True, approver=user.scout):
            tasks.append(task)
        if tasks != []:
            exam.task_list = tasks
            exams.append(exam)
    return render(
        request,
        "exam/check_tasks.html",
        {"user": user, "exams_list": exams},
    )


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
            "tasks_list": Task.objects.filter(is_await=True, exam=exam),
        },
    )


def unsubmit_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if request.user.scout != exam.scout or task.is_await != True or task.exam != exam:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji tego zadania."
        )
        return redirect(reverse("exam:exam"))
    Task.objects.filter(task=task).update(is_await=False, approver=None)
    return redirect(f"/exam/{str(exam_id)}/tasks/sent")


def refuse_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if (
        task.is_await != True
        or task.exam != exam
        or task.approver != request.user.scout
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("exam:check_tasks"))
    Task.objects.filter(task=task).update(is_await=False, approver=None)
    return redirect(reverse("exam:check_tasks"))


def accept_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if (
        task.is_await != True
        or task.exam != exam
        or task.approver != request.user.scout
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do akceptacji tego zadania."
        )
        return redirect(reverse("exam:check_tasks"))
    Task.objects.filter(task=task).update(
        is_await=False, is_done=True, approval_date=datetime.datetime.now()
    )
    return redirect(reverse("exam:check_tasks"))


def force_refuse_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if task.exam != exam or (
        not request.user.scout.is_patrol_leader
        and not request.user.scout.is_team_leader
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("exam:edit_exams"))
    Task.objects.filter(task=task).update(
        is_await=False, is_done=False, approver=None, approval_date=None
    )
    return redirect(reverse("exam:edit_exams"))


def force_accept_task(request, exam_id, task_id):
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if task.exam != exam or (
        not request.user.scout.is_patrol_leader
        and not request.user.scout.is_team_leader
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do zaliczenia tego zadania."
        )
        return redirect(reverse("exam:edit_exams"))
    Task.objects.filter(task=task).update(
        is_await=False,
        is_done=True,
        approver=request.user.scout,
        approval_date=datetime.datetime.now(),
    )
    return redirect(reverse("exam:edit_exams"))


class SumbitTaskForm(forms.ModelForm):
    def __init__(self, request, user, exam, *args, **kwargs):
        super(SumbitTaskForm, self).__init__(*args, **kwargs)
        self.fields["approver"].widget.attrs["required"] = "required"
        if request.user.scout.team:
            query = Q(is_patrol_leader=True)
            query.add(Q(is_team_leader=True), Q.OR)
            query.add(Q(team=request.user.scout.team), Q.AND)
            self.fields["approver"].queryset = Scout.objects.filter(query).exclude(
                user=request.user
            )
        else:
            self.fields["approver"].queryset = Scout.objects.filter(
                Q(is_patrol_leader=True) | Q(is_team_leader=True)
            ).exclude(user=request.user)

    class Meta:
        model = Task
        fields = ["approver"]

        labels = {
            "approver": "Do kogo chcesz wysłać prośbę o zatwierddzenie?*",
        }
        widgets = {
            "approver": Select(),
        }


class SumbitSelectTaskForm(forms.ModelForm):
    def __init__(self, request, user, exam, *args, **kwargs):
        super(SumbitSelectTaskForm, self).__init__(*args, **kwargs)
        for bound_field in self:
            if hasattr(bound_field, "field") and bound_field.field.required:
                bound_field.field.widget.attrs["required"] = "required"
        self.fields["task"].queryset = (
            Task.objects.filter(exam=exam).exclude(is_done=True).exclude(is_await=True)
        )

    class Meta:
        model = SentTask
        fields = ["task"]

        labels = {
            "task": "Wbierz zadanie",
        }
        widgets = {
            "task": Select(),
        }


def submit_task(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user.scout != exam.scout:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("exam:exam"))
    if request.method == "POST":
        submit_select_task_form = SumbitSelectTaskForm(
            request, request.user, exam, request.POST
        )
        if submit_select_task_form.is_valid():
            submited_select_task = submit_select_task_form.save(commit=False)
            submited_select_task.user = request.user

            submited_select_task.save()

        submit_task_form = SumbitTaskForm(
            request,
            request.user,
            exam,
            request.POST,
            instance=submited_select_task.task,
        )
        if submit_task_form.is_valid():
            submited_task = submit_task_form.save(commit=False)
            submited_task.user = request.user
            submited_task.exam = exam
            submited_task.is_await = True
            submited_task.save()

            return redirect(reverse("exam:exam"))

    else:
        submit_task_form = SumbitTaskForm(request=request, user=request.user, exam=exam)
        submit_select_task_form = SumbitSelectTaskForm(
            request=request, user=request.user, exam=exam
        )
    return render(
        request,
        "exam/request_task_check.html",
        {
            "user": request.user,
            "exam": exam,
            "forms": [submit_select_task_form, submit_task_form],
        },
    )
