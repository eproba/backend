from django.contrib import messages
from django.forms import formset_factory, inlineformset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import ExamCreateForm, TaskForm
from ..models import Exam, Task


def edit_exam(request, exam_id):
    exam = Exam.objects.get(pk=exam_id)
    TaskFormSet = inlineformset_factory(Exam, Task, TaskForm, extra=0, can_order=True)
    if request.method == "POST":
        exam_form = ExamCreateForm(request.POST, instance=exam)
        tasks = TaskFormSet(request.POST, instance=exam)
        if exam_form.is_valid():
            exam_obj = exam_form.save()
            if tasks.is_valid():
                for task_form in tasks:
                    if task_form.cleaned_data["DELETE"]:
                        task_form.instance.delete()
                    else:
                        task = Task.objects.get_or_create(id=task_form.instance.id)[0]
                        if task_form.cleaned_data["task"] != task.task:
                            task.status = 1
                            task.task = task_form.cleaned_data["task"]
                        task.order = task_form.cleaned_data["ORDER"]
                        task.save()

            messages.add_message(request, messages.INFO, "Próba została zapisana.")
            return redirect(reverse("exam:manage_exams"))

    else:
        exam_form = ExamCreateForm(instance=exam)
        tasks = TaskFormSet(instance=exam)

    return render(request, "exam/edit_exam.html", {"exam": exam_form, "tasks": tasks})
