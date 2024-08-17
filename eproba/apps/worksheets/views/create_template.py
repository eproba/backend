from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse
from users.utils import min_function, patrol_required

from ..forms import TaskForm, WorksheetCreateForm
from ..models import Task


@login_required
@patrol_required
@min_function(2)
def create_template(request):
    task_form_set = formset_factory(TaskForm, extra=3)
    if request.method == "POST":
        worksheet = WorksheetCreateForm(request.POST)
        tasks = task_form_set(request.POST)
        if worksheet.is_valid():

            worksheet_obj = worksheet.save(commit=False)
            worksheet_obj.is_template = True
            worksheet_obj.user = request.user
            worksheet_obj.save()
            if tasks.is_valid():
                tasks_data = tasks.cleaned_data
                for task in tasks_data:
                    if "task" in task:
                        Task.objects.create(worksheet=worksheet_obj, task=task["task"])
            messages.success(request, "Szablon został utworzony")
            if request.GET.get("next", False):
                return redirect(request.GET.get("next"))
            return redirect(reverse("worksheets:templates"))

    else:
        worksheet = WorksheetCreateForm()
        tasks = task_form_set()

    return render(
        request,
        "worksheets/create_template.html",
        {"worksheet": worksheet, "tasks": tasks},
    )
