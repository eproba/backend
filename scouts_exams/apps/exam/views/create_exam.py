from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import ExamCreateForm, ExtendedExamCreateForm, TaskForm
from ..models import Exam, Task


def create_exam(request):
    if request.GET.get("source", False) == "templates" and request.GET.get(
        "template", False
    ):
        template_id = request.GET.get("template", False)
        template = Exam.objects.get(pk=template_id)
    else:
        template = None
    TaskFormSet = formset_factory(TaskForm, extra=1)
    if request.method == "POST":
        if request.user.scout.function >= 2:
            exam = ExtendedExamCreateForm(request.user, request.POST)
        else:
            exam = ExamCreateForm(request.POST)
        if template:
            tasks = TaskFormSet(
                request.POST,
                initial=[{"task": task.task} for task in template.tasks.all()],
            )
        else:
            tasks = TaskFormSet(request.POST)
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
        if template:
            tasks = TaskFormSet(
                initial=[{"task": task.task} for task in template.tasks.all()]
            )
        else:
            tasks = TaskFormSet()

    return render(request, "exam/create_exam.html", {"exam": exam, "tasks": tasks})
