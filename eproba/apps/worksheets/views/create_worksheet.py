from apps.users.utils import send_notification
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms import ExtendedWorksheetCreateForm, TaskForm, WorksheetCreateForm
from ..models import Task, TemplateWorksheet


@login_required
@transaction.atomic
def create_worksheet(request):
    if request.GET.get("source", False) == "templates" and request.GET.get(
        "template", False
    ):
        template_id = request.GET.get("template", False)
        template = get_object_or_404(TemplateWorksheet, id=template_id)
        task_form_set = formset_factory(TaskForm, extra=1)
    # elif request.GET.get("source", False) == "copy" and request.GET.get(
    #     "worksheet", False
    # ):
    #     template_id = request.GET.get("worksheet", False)
    #     template = get_object_or_404(Worksheet, id=template_id, deleted=False)
    #     task_form_set = formset_factory(TaskForm, extra=1)
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
                initial=[
                    {"task": task.task, "description": task.description}
                    for task in template.tasks.all()
                ],
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

            if request.user != worksheet_obj.user:
                send_notification(
                    targets=worksheet_obj.user,
                    title="Nowa próba",
                    body="Została utworzona nowa próba dla ciebie.",
                    link=reverse(
                        "worksheets:worksheet_detail",
                        kwargs={
                            "id": worksheet_obj.id,
                        },
                    ),
                )
            messages.success(request, "Próba została utworzona")
            if request.GET.get("next", False):
                return redirect(request.GET.get("next"))
            return redirect(reverse("worksheets:worksheets"))
        else:
            messages.error(request, "Błąd w formularzu")

    else:
        if request.user.function >= 2 and request.user.patrol:
            worksheet = ExtendedWorksheetCreateForm(
                request.user,
                template_notes=template.template_notes if template else None,
            )
        else:
            worksheet = WorksheetCreateForm(
                template_notes=template.template_notes if template else None
            )
        if template:
            tasks = task_form_set(
                initial=[
                    {
                        "task": task.task,
                        "description": task.description,
                        "template_notes": task.template_notes,
                    }
                    for task in template.tasks.all()
                ]
            )
            worksheet.fields["name"].initial = template.name
            worksheet.fields["description"].initial = template.description
            worksheet.fields["user"].initial = None
        else:
            tasks = task_form_set()

    return render(
        request,
        "worksheets/create_worksheet.html",
        {"worksheet": worksheet, "tasks": tasks},
    )
