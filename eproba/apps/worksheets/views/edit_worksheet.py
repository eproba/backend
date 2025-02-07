from apps.users.utils import min_function
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import TaskForm, WorksheetCreateForm
from ..models import Task, Worksheet


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


@login_required
@min_function(2)
def edit_worksheet(request, worksheet_id):
    if not Worksheet.objects.filter(id=worksheet_id, deleted=False).exists():
        messages.add_message(request, messages.ERROR, "Nie ma takiej próby.")
        return redirect(reverse("worksheets:manage_worksheets"))
    if request.user.function == 2:
        if (
            Worksheet.objects.get(id=worksheet_id, deleted=False).user.patrol.team
            != request.user.patrol.team
        ):
            messages.add_message(
                request,
                messages.ERROR,
                "Nie masz uprawnień do edycji prób z poza swojej drużyny.",
            )
            return redirect(reverse("worksheets:worksheets"))
    worksheet = Worksheet.objects.get(id=worksheet_id, deleted=False)
    task_form_set = formset_factory(TaskForm, extra=1)
    if request.method == "POST":
        worksheet_form = WorksheetCreateForm(request.POST, instance=worksheet)
        tasks = task_form_set(request.POST)
        if worksheet_form.is_valid():
            worksheet_obj = worksheet_form.save()
            if tasks.is_valid():
                old_tasks = []
                for task in Task.objects.filter(worksheet=worksheet_obj):
                    task.delete()
                    old_tasks.append(task)
                for task in remove_duplicates(
                    [
                        (t["task"], t["description"])
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
                        t = Task(
                            task=task[0], worksheet=worksheet_obj, description=task[1]
                        )
                        t.save()
                if worksheet_obj.is_template:
                    messages.info(request, "Szablon został zapisany.")
                else:
                    messages.info(request, "Próba została zapisana.")
            else:
                messages.add_message(request, messages.ERROR, "Błąd w zadaniach.")
            if worksheet_obj.is_template:
                return redirect(reverse("worksheets:templates"))
            return redirect(reverse("worksheets:manage_worksheets"))

    else:
        worksheet_form = WorksheetCreateForm(instance=worksheet)
        tasks = task_form_set(
            initial=[
                {"task": task.task, "description": task.description}
                for task in worksheet.tasks.all()
            ]
        )

    return render(
        request,
        "worksheets/edit_worksheet.html",
        {"worksheet": worksheet_form, "tasks": tasks},
    )
