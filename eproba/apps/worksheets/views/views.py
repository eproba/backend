from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from fcm_django.models import FCMDevice
from firebase_admin.messaging import (
    Message,
    WebpushConfig,
    WebpushFCMOptions,
    WebpushNotification,
)

from ...teams.models import Patrol
from ..forms import SubmitTaskForm
from ..models import Task, Worksheet
from .utils import prepare_worksheet

# from weasyprint import HTML


def view_worksheets(request):
    if request.user.is_authenticated:
        user = request.user
        worksheets = [
            prepare_worksheet(worksheet)
            for worksheet in Worksheet.objects.filter(
                user=user, is_template=False, deleted=False, is_archived=False
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

    # response = HttpResponse(
    #     HTML(string=render_to_string("worksheets/worksheet_pdf.html", {"worksheet": worksheet})).write_pdf(),
    #     content_type="application/pdf",
    # )
    # response["Content-Disposition"] = (
    #     f'inline; filename="{unidecode(str(worksheets))} (Epróba).pdf"'
    # )
    #
    # return response
    return HttpResponse("Not implemented", status=501)


def view_shared_worksheet(request, id):
    user = request.user
    worksheet = get_object_or_404(Worksheet, id=id, deleted=False, is_archived=False)
    return render(
        request,
        "worksheets/worksheet.html",
        {"user": user, "worksheets_list": [worksheet], "is_shared": True},
    )


def manage_worksheets(request):
    if not request.user.is_authenticated:
        return render(request, "worksheets/manage_worksheets.html")
    if not request.user.patrol:
        messages.error(request, "Nie jesteś przypisany do żadnej drużyny.")
        return render(request, "worksheets/manage_worksheets.html")
    user = request.user

    if request.user.function < 2:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji prób."
        )
        return redirect(reverse("worksheets:worksheets"))

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
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
        return redirect(reverse("worksheets:worksheets"))
    return render(
        request,
        "worksheets/sent_tasks.html",
        {
            "user": request.user,
            "worksheets": worksheet,
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
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1 or task.worksheet != worksheet or task.approver != request.user:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("worksheets:check_tasks"))
    Task.objects.filter(id=task.id).update(status=3)
    worksheet.save()  # update worksheets's last modification date
    return redirect(reverse("worksheets:check_tasks"))


def accept_task(request, worksheet_id, task_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if task.status != 1 or task.worksheet != worksheet or task.approver != request.user:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do akceptacji tego zadania."
        )
        return redirect(reverse("worksheets:check_tasks"))
    Task.objects.filter(id=task.id).update(status=2, approval_date=timezone.now())
    worksheet.save()  # update worksheets's last modification date
    return redirect(reverse("worksheets:check_tasks"))


def force_reject_task(request, worksheet_id, task_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        if (
            task.worksheet != worksheet
            or request.user.function < 2
            or request.user.function < worksheet.user.function
        ):
            return HttpResponse("401 Unauthorized", status=401)
        Task.objects.filter(id=task.id).update(status=3, approver=request.user)
        worksheet.save()  # update worksheets's last modification date
        return HttpResponse("OK", status=200)
    if (
        task.worksheet != worksheet
        or request.user.function < 2
        or request.user.function < worksheet.user.function
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do odrzucenia tego zadania."
        )
        return redirect(reverse("worksheets:edit_worksheets"))
    Task.objects.filter(id=task.id).update(status=3, approver=None)
    return redirect(reverse("worksheets:edit_worksheets"))


def force_accept_task(request, worksheet_id, task_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        if (
            task.worksheet != worksheet
            or request.user.function < 2
            or request.user.function < worksheet.user.function
        ):
            return HttpResponse("401 Unauthorized", status=401)
        Task.objects.filter(id=task.id).update(
            status=2,
            approver=request.user,
            approval_date=timezone.now(),
        )
        worksheet.save()  # update worksheets's last modification date
        return HttpResponse("OK", status=200)
    if (
        task.worksheet != worksheet
        or request.user.function < 2
        or request.user.function < worksheet.user.function
    ):
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do zaliczenia tego zadania."
        )
        return redirect(reverse("worksheets:edit_worksheets"))
    Task.objects.filter(id=task.id).update(
        status=2,
        approver=request.user,
        approval_date=timezone.now(),
    )
    return redirect(reverse("worksheets:edit_worksheets"))


def submit_task(request, worksheet_id):
    worksheet = get_object_or_404(Worksheet, id=worksheet_id, deleted=False)
    if request.user != worksheet.user:
        messages.add_message(request, messages.INFO, "Nie masz dostępu do tej próby.")
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
            submitted_task.user = request.user
            submitted_task.worksheet = worksheet
            submitted_task.approval_date = timezone.now()
            submitted_task.status = 1
            submitted_task.save()

            FCMDevice.objects.filter(user=submitted_task.approver.user).send_message(
                Message(
                    webpush=WebpushConfig(
                        notification=WebpushNotification(
                            title="Nowe zadanie do sprawdzenia",
                            body=f"Pojawił się nowy punkt do sprawdzenia dla {submitted_task.user}.",
                        ),
                        fcm_options=WebpushFCMOptions(
                            link="https://"
                            + request.get_host()
                            + reverse("worksheets:check_tasks")
                        ),
                    ),
                )
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
