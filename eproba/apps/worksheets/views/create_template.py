from apps.users.utils import min_function, patrol_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import TemplateTaskForm, TemplateWorksheetCreateForm
from ..models import TemplateTask


@login_required
@patrol_required
@min_function(2)
def create_template(request):
    task_form_set = formset_factory(TemplateTaskForm, extra=3)
    if request.method == "POST":
        worksheet_template = TemplateWorksheetCreateForm(request.POST)
        tasks = task_form_set(request.POST)
        if worksheet_template.is_valid():

            worksheet_template_obj = worksheet_template.save(commit=False)
            worksheet_template_obj.team = request.user.patrol.team
            worksheet_template_obj.save()
            if tasks.is_valid():
                tasks_data = tasks.cleaned_data
                for task in tasks_data:
                    if "task" in task:
                        TemplateTask.objects.create(
                            template=worksheet_template_obj,
                            task=task["task"],
                            description=task["description"],
                            template_notes=task["template_notes"],
                        )
            messages.success(request, "Szablon został utworzony")
            if request.GET.get("next", False):
                return redirect(request.GET.get("next"))
            return redirect(reverse("worksheets:templates"))

    else:
        worksheet_template = TemplateWorksheetCreateForm()
        tasks = task_form_set()

    return render(
        request,
        "worksheets/create_template.html",
        {"worksheet": worksheet_template, "tasks": tasks},
    )
