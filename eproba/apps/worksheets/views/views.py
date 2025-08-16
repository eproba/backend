from apps.users.utils import min_function, patrol_required, send_notification
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from unidecode import unidecode

try:
    from weasyprint import HTML
except OSError:
    pass

from apps.worksheets.utils import prepare_worksheet

from ...teams.models import Patrol
from ..forms import SubmitTaskForm
from ..models import Task, TemplateWorksheet, Worksheet


def view_worksheets(request):
    if request.user.is_authenticated:
        user = request.user
        worksheets = [
            prepare_worksheet(worksheet)
            for worksheet in Worksheet.objects.filter(
                user=user, deleted=False, is_archived=False
            )
        ]

        return render(
            request,
            "worksheets/worksheet.html",
            {"user": user, "worksheets_list": worksheets},
        )
    return render(
        request,
        "worksheets/worksheet.html",
        {"user": request.user, "worksheets_list": []},
    )


def print_worksheet(request, id):
    worksheet = get_object_or_404(Worksheet, id=id)
    # Prepare task lists ordered by 'order'
    tasks_qs = worksheet.tasks.all().order_by("order")
    general_tasks = list(tasks_qs.filter(category="general"))
    individual_tasks = list(tasks_qs.filter(category="individual"))
    has_both = bool(general_tasks) and bool(individual_tasks)

    try:
        response = HttpResponse(
            HTML(
                string=render_to_string(
                    "worksheets/worksheet_pdf.html",
                    {
                        "worksheet": worksheet,
                        "all_tasks": list(tasks_qs),
                        "general_tasks": general_tasks,
                        "individual_tasks": individual_tasks,
                        "has_both_categories": has_both,
                    },
                ),
                base_url=request.build_absolute_uri(),
            ).write_pdf(),
            content_type="application/pdf",
        )
    except NameError:
        return HttpResponse(
            "Weasyprint is not installed, PDF generation is not possible.\nContact the administrator for help.",
            content_type="text/plain",
            status=500,
        )
    response["Content-Disposition"] = (
        f'inline; filename="{unidecode(str(worksheet))} - Epróba.pdf"'
    )

    return response


def print_worksheet_template(request, id):
    worksheet_template = get_object_or_404(TemplateWorksheet, id=id)

    # Template tasks ordered by 'order'
    tasks_qs = worksheet_template.tasks.all().order_by("order")
    general_tasks = list(tasks_qs.filter(category="general"))
    individual_tasks = list(tasks_qs.filter(category="individual"))
    has_both = bool(general_tasks) and bool(individual_tasks)
    try:
        response = HttpResponse(
            HTML(
                string=render_to_string(
                    "worksheets/worksheet_pdf.html",
                    {
                        "worksheet": worksheet_template,
                        "is_template": True,
                        "all_tasks": list(tasks_qs),
                        "general_tasks": general_tasks,
                        "individual_tasks": individual_tasks,
                        "has_both_categories": has_both,
                    },
                ),
                base_url=request.build_absolute_uri(),
            ).write_pdf(),
            content_type="application/pdf",
        )
    except NameError:
        return HttpResponse(
            "Weasyprint is not installed, PDF generation is not possible.\nContact the administrator for help.",
            content_type="text/plain",
            status=500,
        )
    response["Content-Disposition"] = (
        f'inline; filename="{unidecode(str(worksheet_template))} - Epróba.pdf"'
    )

    return response


def view_shared_worksheet(request, id):
    user = request.user
    worksheet = get_object_or_404(Worksheet, id=id, deleted=False, is_archived=False)
    return render(
        request,
        "worksheets/worksheet.html",
        {"user": user, "worksheets_list": [worksheet], "is_shared": True},
    )


@patrol_required
@min_function(2)
def manage_worksheets(request):
    user = request.user

    patrols = Patrol.objects.filter(team__id=user.patrol.team.id).order_by("name")
    return render(
        request,
        "worksheets/manage_worksheets.html",
        {"user": user, "patrols": patrols},
    )


def check_tasks(request):
    if not request.user.is_authenticated:
        return render(request, "worksheets/check_tasks.html")
    user = request.user
    worksheets = []
    if user.function >= 2:
        for worksheet in Worksheet.objects.filter(deleted=False, is_archived=False):
            if tasks := list(worksheet.tasks.filter(status=1, approver=user)):
                worksheet.task_list = tasks
                worksheets.append(worksheet)
        return render(
            request,
            "worksheets/check_tasks.html",
            {"user": user, "worksheets_list": worksheets},
        )
    messages.add_message(
        request, messages.INFO, "Nie masz uprawnień do akceptacji zadań."
    )
    return redirect(reverse("worksheets:worksheets"))


def sent_tasks(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id)
    if request.user != worksheet.user:
        messages.info(request, "Nie masz dostępu do tej próby.")
        return redirect(reverse("worksheets:worksheets"))
    return render(
        request,
        "worksheets/sent_tasks.html",
        {
            "user": request.user,
            "worksheet": worksheet,
            "tasks_list": Task.objects.filter(status=1, worksheet=worksheet),
        },
    )


def unsubmit_task(request, worksheet_id, task_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if (
        request.user != worksheet.user
        or task.status != 1
        or task.worksheet != worksheet
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji tego zadania."
        )
        return redirect(reverse("worksheets:worksheets"))
    Task.objects.filter(task=task).update(status=0, approver=None)
    return redirect(f"/worksheets/{str(worksheet_id)}/tasks/sent")


def reject_task(request, worksheet_id, task_id):
    """Rejects a task that was submitted for approval."""
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1:
        messages.add_message(
            request, messages.INFO, "To zadanie nie jest już do sprawdzenia."
        )
        return redirect(reverse("worksheets:check_tasks"))
    if task.worksheet != worksheet or task.approver != request.user:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("worksheets:check_tasks"))
    Task.objects.filter(id=task.id).update(status=3)
    worksheet.save()  # update worksheets's last modification date
    send_notification(
        targets=task.worksheet.user,
        title="Zadanie odrzucone",
        body=f"Twoje zadanie w próbie {worksheet} zostało odrzucone.",
        link=reverse("worksheets:worksheets"),
    )
    return redirect(reverse("worksheets:check_tasks"))


def accept_task(request, worksheet_id, task_id):
    """Accepts a task that was submitted for approval."""
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1:
        messages.add_message(
            request, messages.INFO, "To zadanie nie jest już do sprawdzenia."
        )
        return redirect(reverse("worksheets:check_tasks"))
    if task.worksheet != worksheet or task.approver != request.user:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do akceptacji tego zadania."
        )
        return redirect(reverse("worksheets:check_tasks"))
    Task.objects.filter(id=task.id).update(status=2, approval_date=timezone.now())
    worksheet.save()  # update worksheets's last modification date
    send_notification(
        targets=task.worksheet.user,
        title="Zadanie zaakceptowane",
        body=f"Twoje zadanie w próbie {worksheet} zostało zaakceptowane.",
        link=reverse("worksheets:worksheets"),
    )
    return redirect(reverse("worksheets:check_tasks"))


def submit_task(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    if request.user != worksheet.user:
        messages.info(request, "Nie masz dostępu do tej próby.")
        return redirect(reverse("worksheets:worksheets"))
    if request.method == "POST":
        submit_task_form = SubmitTaskForm(
            request,
            worksheet,
            request.POST,
            instance=Task.objects.get(id=request.POST.__getitem__("task")),
        )
        if submit_task_form.is_valid():
            submitted_task = submit_task_form.save(commit=False)
            submitted_task.worksheet = worksheet
            submitted_task.approval_date = timezone.now()
            submitted_task.status = 1
            submitted_task.save()

            send_notification(
                targets=submitted_task.approver,
                title="Nowe zadanie do sprawdzenia",
                body=f"Pojawił się nowy punkt do sprawdzenia dla {worksheet.user}",
                link=reverse("worksheets:check_tasks"),
            )
            messages.success(
                request, "Prośba o zaakceptowanie zadania została wysłana."
            )
            return redirect(reverse("worksheets:worksheets"))

    else:
        submit_task_form = SubmitTaskForm(request=request, worksheet=worksheet)
    return render(
        request,
        "worksheets/request_task_check.html",
        {
            "user": request.user,
            "worksheet": worksheet,
            "forms": [submit_task_form],
        },
    )
