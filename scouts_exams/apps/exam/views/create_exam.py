from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from fcm_django.models import FCMDevice
from firebase_admin.messaging import (
    Message,
    WebpushConfig,
    WebpushFCMOptions,
    WebpushNotification,
)
from unidecode import unidecode

from ..forms import ExamCreateForm, ExtendedExamCreateForm, TaskForm
from ..models import Exam, Task


@login_required
def create_exam(request):
    if request.GET.get("source", False) == "templates" and request.GET.get(
        "template", False
    ):
        template_id = request.GET.get("template", False)
        template = get_object_or_404(Exam, id=template_id, deleted=False)
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

            FCMDevice.objects.filter(user=exam_obj.scout.user).send_message(
                Message(
                    webpush=WebpushConfig(
                        notification=WebpushNotification(
                            title="Nowa próba",
                            body="Została utworzona nowa próba dla ciebie.",
                        ),
                        fcm_options=WebpushFCMOptions(
                            link="https://"
                            + request.get_host()
                            + reverse(
                                "exam:exam_detail",
                                kwargs={
                                    "hex": f"{''.join('{:02x}'.format(ord(c)) for c in unidecode(exam_obj.scout.user.nickname))}{hex(exam_obj.scout.user.id * 7312)}{hex(exam_obj.id * 2137)}"
                                },
                            )
                        ),
                    ),
                )
            )
            messages.success(request, "Próba została utworzona")
            if request.GET.get("next", False):
                return redirect(request.GET.get("next"))
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
