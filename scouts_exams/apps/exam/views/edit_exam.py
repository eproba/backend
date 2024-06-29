from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import ExamCreateForm, TaskForm
from ..models import Exam, Task


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def edit_exam(request, exam_id):
    if not request.user.is_authenticated:
        return render(request, "exam/manage_exams.html")
    if request.user.scout.function < 2:
        messages.add_message(
            request, messages.INFO, "Nie masz uprawnień do edycji prób."
        )
        return redirect(reverse("exam:exam"))
    if not Exam.objects.filter(id=exam_id, deleted=False).exists():
        messages.add_message(request, messages.ERROR, "Nie ma takiej próby.")
        return redirect(reverse("exam:manage_exams"))
    if request.user.scout.function == 2:
        if (
            Exam.objects.get(id=exam_id, deleted=False).scout.patrol.team
            != request.user.scout.patrol.team
        ):
            messages.add_message(
                request,
                messages.ERROR,
                "Nie masz uprawnień do edycji prób z poza swojej drużyny.",
            )
            return redirect(reverse("exam:exam"))
    exam = Exam.objects.get(id=exam_id, deleted=False)
    TaskFormSet = formset_factory(TaskForm, extra=1)
    if request.method == "POST":
        exam_form = ExamCreateForm(request.POST, instance=exam)
        tasks = TaskFormSet(request.POST)
        if exam_form.is_valid():
            exam_obj = exam_form.save()
            if tasks.is_valid():
                old_tasks = []
                for task in Task.objects.filter(exam=exam_obj):
                    task.delete()
                    old_tasks.append(task)
                for task in remove_duplicates(
                    [t["task"] for t in tasks.cleaned_data if "task" in t]
                ):
                    if any(x.task == task for x in old_tasks):
                        t = next((x for x in old_tasks if x.task == task), None)
                        t.id = None
                        t.save()
                    else:
                        t = Task(task=task, exam=exam_obj)
                        t.save()
                messages.add_message(request, messages.INFO, "Próba została zapisana.")
            else:
                messages.add_message(request, messages.ERROR, "Błąd w zadaniach.")
            return redirect(reverse("exam:manage_exams"))

    else:
        exam_form = ExamCreateForm(instance=exam)
        tasks = TaskFormSet(initial=[{"task": task.task} for task in exam.tasks.all()])

    return render(request, "exam/edit_exam.html", {"exam": exam_form, "tasks": tasks})
