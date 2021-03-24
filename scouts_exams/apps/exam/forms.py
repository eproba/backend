from django.forms import ModelForm, TextInput

from .models import Exam, Task


class ExamCreateForm(ModelForm):
    class Meta:
        model = Exam
        fields = ["name"]
        labels = {
            "name": "Nazwa próby",
        }


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ["task"]
        labels = {
            "task": "Zadanie",
        }
        widgets = {
            "task": TextInput(attrs={"class": "input"}),
        }
