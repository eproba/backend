from django import forms
from django.contrib import messages
from django.db.models import Q
from django.forms import Select
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from ..teams.models import Patrol
from ..users.models import Scout, User
from .models import Exam, SentTask, Task


def view_exams(request):
    user = request.user
    return render(
        request,
        "exam/exam.html",
        {"user": user, "exams_list": Exam.objects.filter(scout=user.id)},
    )


def sent_tasks(request, user_id, exam_id):
    user = get_object_or_404(User, id=user_id)
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user != user or request.user.scout != exam.scout:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("exam:exam"))
    return render(
        request,
        "exam/sent_tasks.html",
        {
            "user": user,
            "exam": exam,
            "tasks_list": Task.objects.filter(is_await=True, exam=exam),
        },
    )


def unsubmit_task(request, user_id, exam_id, task_id):
    user = get_object_or_404(User, id=user_id)
    exam = get_object_or_404(Exam, id=exam_id)
    task = get_object_or_404(Task, id=task_id)
    if (
        request.user != user
        or request.user.scout != exam.scout
        or task.is_await != True
        or task.exam != exam
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji tego zadania."
        )
        return redirect(reverse("exam:exam"))
    Task.objects.filter(task=task).update(is_await=False, approver=None)
    return redirect(f"/exam/{str(user_id)}/{str(exam_id)}/tasks/sent")


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


def sumbit_task(request, user_id, exam_id):
    user = get_object_or_404(User, id=user_id)
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user != user or request.user.scout != exam.scout:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("exam:exam"))
    if request.method == "POST":
        sumbit_select_task_form = SumbitSelectTaskForm(
            request, user, exam, request.POST
        )
        if sumbit_select_task_form.is_valid():
            sumbited_select_task = sumbit_select_task_form.save(commit=False)
            sumbited_select_task.user = request.user

            sumbited_select_task.save()

        sumbit_task_form = SumbitTaskForm(
            request, user, exam, request.POST, instance=sumbited_select_task.task
        )
        if sumbit_task_form.is_valid():
            sumbited_task = sumbit_task_form.save(commit=False)
            sumbited_task.user = request.user
            sumbited_task.exam = exam
            sumbited_task.is_await = True
            sumbited_task.save()

            return redirect(reverse("exam:exam"))

    else:
        sumbit_task_form = SumbitTaskForm(request=request, user=user, exam=exam)
        sumbit_select_task_form = SumbitSelectTaskForm(
            request=request, user=user, exam=exam
        )
    return render(
        request,
        "exam/request_task_check.html",
        {
            "user": user,
            "exam": exam,
            "forms": [sumbit_select_task_form, sumbit_task_form],
        },
    )
