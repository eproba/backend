from apps.users.utils import min_function, patrol_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import (
    ExtendedTemplateWorksheetCreateForm,
    TemplateTaskForm,
    TemplateWorksheetCreateForm,
)
from ..models import TemplateTask, TemplateWorksheet


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


@login_required
@patrol_required
@min_function(2)
def edit_template(request, worksheet_id):
    if not TemplateWorksheet.objects.filter(id=worksheet_id).exists():
        messages.add_message(request, messages.ERROR, "Nie ma takiego szablonu.")
        return redirect(reverse("worksheets:templates"))
    worksheet = TemplateWorksheet.objects.get(id=worksheet_id)
    if worksheet.team != request.user.patrol.team and not (
        worksheet.organization == request.user.patrol.team.organization
        and request.user.has_perm("worksheets.change_templateworksheet")
        and request.user.is_staff
    ):
        messages.add_message(
            request,
            messages.ERROR,
            "Nie masz uprawnień do edycji tego szablonu.",
        )
        return redirect(reverse("worksheets:templates"))
    task_form_set = formset_factory(TemplateTaskForm, extra=1)
    if request.method == "POST":
        if request.user.has_perm("worksheets.change_templateworksheet"):
            worksheet_form = ExtendedTemplateWorksheetCreateForm(
                request.POST, instance=worksheet
            )
        else:
            worksheet_form = TemplateWorksheetCreateForm(
                request.POST, instance=worksheet
            )
        tasks = task_form_set(request.POST)
        if worksheet_form.is_valid():
            worksheet_obj = worksheet_form.save(commit=False)
            if worksheet_form.cleaned_data.get("for_organization"):
                if not request.user.is_staff or not request.user.has_perm(
                    "worksheets.change_templateworksheet"
                ):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Nie masz uprawnień do edycji szablonów dla całej organizacji.",
                    )
                    return redirect(reverse("worksheets:templates"))
                worksheet_obj.team = None
                worksheet_obj.organization = request.user.patrol.team.organization
            else:
                worksheet_obj.team = request.user.patrol.team
                worksheet_obj.organization = None
            worksheet_obj.save()
            if tasks.is_valid():
                old_tasks = []
                for task in TemplateTask.objects.filter(template=worksheet_obj):
                    task.delete()
                    old_tasks.append(task)
                for task in remove_duplicates(
                    [
                        (t["task"], t["description"], t["template_notes"])
                        for t in tasks.cleaned_data
                        if "task" in t
                    ]
                ):
                    if any(x.task == task for x in old_tasks):
                        t = next(
                            (x for x in old_tasks if (x.task, x.description) == task),
                            None,
                        )
                        t.id = None
                        t.save()
                    else:
                        t = TemplateTask(
                            task=task[0],
                            template=worksheet_obj,
                            description=task[1],
                            template_notes=task[2],
                        )
                        t.save()
                messages.info(request, "Szablon został zaktualizowany.")
                return redirect(reverse("worksheets:templates"))
            else:
                messages.add_message(request, messages.ERROR, "Błąd w zadaniach.")

    else:
        if request.user.has_perm("worksheets.change_templateworksheet"):
            worksheet_form = ExtendedTemplateWorksheetCreateForm(
                instance=worksheet,
                initial={"for_organization": worksheet.organization is not None},
            )
        else:
            worksheet_form = TemplateWorksheetCreateForm(instance=worksheet)
        tasks = task_form_set(
            initial=[
                {
                    "task": task.task,
                    "description": task.description,
                    "template_notes": task.template_notes,
                }
                for task in worksheet.tasks.all()
            ]
        )

    return render(
        request,
        "worksheets/edit_template.html",
        {"worksheet": worksheet_form, "tasks": tasks},
    )
