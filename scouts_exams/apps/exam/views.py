import datetime

from django import forms
from django.contrib import messages
from django.db.models import Q
from django.forms import Select
from django.forms.formsets import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from unidecode import unidecode
from weasyprint import HTML

from ..users.models import Scout
from .forms import ExamCreateForm, TaskForm
from .models import Exam, SentTask, Task


def view_exams(request):
    if request.user.is_authenticated:
        user = request.user
        exams = []
        for exam in Exam.objects.filter(scout__user=user):
            _all = 0
            _done = 0
            for task in exam.tasks.all():
                _all += 1
                if task.status == 2:
                    _done += 1
            if _all != 0:
                percent = int(round(_done / _all, 2) * 100)
                exam.percent = f"{str(percent)}%"
            else:
                exam.percent = "Nie masz jeszcze żadnych zadań"
            exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id * 7312)}{hex(exam.id * 2137)}"
            exams.append(exam)
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

        _all = 0
        _done = 0
        for task in exam.tasks.all():
            _all += 1
            if task.status == 2:
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
    if not request.user.is_authenticated:
        return render(request, "exam/edit_exams.html")
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
            _all = 0
            _done = 0
            for task in exam.tasks.all():
                _all += 1
                if task.status == 2:
                    _done += 1
            if _all != 0:
                percent = int(round(_done / _all, 2) * 100)
                exam.percent = f"{str(percent)}%"
            else:
                exam.percent = "Ta próba nie ma jeszcze dodanych żadnych zadań"
            exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id * 7312)}{hex(exam.id * 2137)}"
            exams.append(exam)
    elif request.user.scout.function == 3 or request.user.scout.function == 4:
        for exam in Exam.objects.filter(scout__team__id=user.scout.team.id):
            _all = 0
            _done = 0
            for task in exam.tasks.all():
                _all += 1
                if task.status == 2:
                    _done += 1
            if _all != 0:
                percent = int(round(_done / _all, 2) * 100)
                exam.percent = f"{str(percent)}%"
            else:
                exam.percent = "Ta próba nie ma jeszcze dodanych żadnych zadań"
            exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id * 7312)}{hex(exam.id * 2137)}"
            exams.append(exam)
    elif request.user.scout.function >= 5:
        for exam in Exam.objects.filter(scout__team__id=user.scout.team.id):
            _all = 0
            _done = 0
            for task in exam.tasks.all():
                _all += 1
                if task.status == 2:
                    _done += 1
            if _all != 0:
                percent = int(round(_done / _all, 2) * 100)
                exam.percent = f"{str(percent)}%"
            else:
                exam.percent = "Ta próba nie ma jeszcze dodanych żadnych zadań"
            exam.share_key = f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam.scout.user.nickname))}{hex(exam.scout.user.id * 7312)}{hex(exam.id * 2137)}"
            exams.append(exam)
    return render(
        request,
        "exam/edit_exams.html",
        {"user": user, "exams_list": exams},
    )


def create_exam(request):
    TaskFormSet = formset_factory(TaskForm, extra=1)
    if request.method == "POST":
        exam = ExamCreateForm(request.POST)
        tasks = TaskFormSet(request.POST, initial=[{"task": " "}])

        if exam.is_valid():
            exam_obj = exam.save()
            exam_obj.scout = request.user.scout
            exam_obj.save()
            if tasks.is_valid():
                tasks_data = tasks.cleaned_data
                for task in tasks_data:
                    if "task" in task:
                        Task.objects.create(exam=exam_obj, task=task["task"])

            messages.add_message(request, messages.INFO, "Próba została utworzona.")
            return redirect(reverse("exam:exam"))

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
    Task.objects.filter(id=task.id).update(
        status=2, approval_date=datetime.datetime.now()
    )
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
            approval_date=datetime.datetime.now(),
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
            approval_date=datetime.datetime.now(),
        )
        return redirect(reverse("exam:edit_exams"))


class SumbitTaskForm(forms.ModelForm):
    def __init__(self, request, user, exam, *args, **kwargs):
        super(SumbitTaskForm, self).__init__(*args, **kwargs)
        self.fields["approver"].widget.attrs["required"] = "required"
        if request.user.scout.team:
            query = Q(function__gte=2)
            query.add(Q(function__gt=request.user.scout.function), Q.AND)
            query.add(Q(team=request.user.scout.team), Q.AND)
            self.fields["approver"].queryset = Scout.objects.filter(query).exclude(
                user=request.user
            )
        else:
            self.fields["approver"].queryset = Scout.objects.filter(
                Q(function__gte=2)
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
            Task.objects.filter(exam=exam).exclude(status=1).exclude(status=2)
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
            submited_task.status = 1
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
