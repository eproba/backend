from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
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

from ..forms import ExtendedWorksheetCreateForm, TaskForm, WorksheetCreateForm
from ..models import Task, Worksheet


@login_required
@transaction.atomic
def create_worksheet(request):
    if request.GET.get("source", False) == "templates" and request.GET.get(
        "template", False
    ):
        template_id = request.GET.get("template", False)
        template = get_object_or_404(Worksheet, id=template_id, deleted=False)
        task_form_set = formset_factory(TaskForm, extra=1)
    else:
        template = None
        task_form_set = formset_factory(TaskForm, extra=3)
    if request.method == "POST":
        if request.user.function >= 2 and request.user.patrol:
            worksheet = ExtendedWorksheetCreateForm(request.user, request.POST)
        else:
            worksheet = WorksheetCreateForm(request.POST)
        if template:
            tasks = task_form_set(
                request.POST,
                initial=[{"task": task.task} for task in template.tasks.all()],
            )
        else:
            tasks = task_form_set(request.POST)
        if worksheet.is_valid():
            if request.user.function >= 2 and request.user.patrol:
                worksheet_obj = worksheet.save()
            else:
                worksheet_obj = worksheet.save(commit=False)
                worksheet_obj.user = request.user
                worksheet_obj.save()
            if tasks.is_valid():
                tasks_data = tasks.cleaned_data
                for task in tasks_data:
                    if "task" in task:
                        Task.objects.create(
                            worksheet=worksheet_obj,
                            task=task["task"],
                            description=task["description"],
                        )

            FCMDevice.objects.filter(user=worksheet_obj.user).send_message(
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
                                "worksheets:worksheet_detail",
                                kwargs={
                                    "id": worksheet_obj.id,
                                },
                            )
                        ),
                    ),
                )
            )
            messages.success(request, "Próba została utworzona")
            if request.GET.get("next", False):
                return redirect(request.GET.get("next"))
            return redirect(reverse("worksheets:worksheets"))

    else:
        if request.user.function >= 2 and request.user.patrol:
            worksheet = ExtendedWorksheetCreateForm(request.user)
        else:
            worksheet = WorksheetCreateForm()
        if template:
            tasks = task_form_set(
                initial=[{"task": task.task} for task in template.tasks.all()]
            )
        else:
            tasks = task_form_set()

    return render(
        request,
        "worksheets/create_worksheet.html",
        {"worksheet": worksheet, "tasks": tasks},
    )
