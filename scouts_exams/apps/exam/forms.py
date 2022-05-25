from django import forms
from django.db.models import Q
from django.forms import ModelForm, Select, TextInput

from ..users.models import Scout
from .models import Exam, Task


class ExamCreateForm(ModelForm):
    class Meta:
        model = Exam
        fields = ["name"]
        labels = {
            "name": "Nazwa próby",
        }
        widgets = {
            "name": TextInput(
                attrs={"class": "input textInput form-control is-colored"}
            ),
        }


class ExtendedExamCreateForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ExtendedExamCreateForm, self).__init__(*args, **kwargs)
        self.fields["scout"].required = True
        self.initial["scout"] = user.scout
        if user.scout.patrol.team and not user.scout.function >= 5:
            self.fields["scout"].queryset = Scout.objects.filter(
                patrol__team=user.scout.patrol.team
            )

    class Meta:
        model = Exam
        fields = ["scout", "name"]
        labels = {
            "scout": "Dla kogo chcesz stworzyć próbę?",
            "name": "Nazwa próby",
        }
        widgets = {
            "scout": Select(attrs={"class": "select form-control is-colored"}),
            "name": TextInput(
                attrs={"class": "input textInput form-control is-colored"}
            ),
        }


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ["task"]
        labels = {
            "task": "Zadanie",
        }
        widgets = {
            "task": TextInput(attrs={"class": "input is-colored"}),
        }


class SubmitTaskForm(forms.ModelForm):
    def __init__(self, request, user, exam, *args, **kwargs):
        super(SubmitTaskForm, self).__init__(*args, **kwargs)
        self.fields["approver"].widget.attrs["required"] = "required"
        if request.user.scout.patrol.team:
            query = Q(function__gte=2)
            query.add(Q(function__gt=request.user.scout.function), Q.AND)
            query.add(Q(patrol__team=request.user.scout.patrol.team), Q.AND)
            self.fields["approver"].queryset = Scout.objects.filter(query).exclude(
                user=request.user
            )
        else:
            self.fields["approver"].queryset = Scout.objects.filter(
                Q(function__gte=2)
            ).exclude(user=request.user)
        self.fields["task"].queryset = (
            Task.objects.filter(exam=exam).exclude(status=1).exclude(status=2)
        )
        self.fields["task"].label = "Wybierz zadanie do przesłania"

    task = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = Task
        fields = ["task", "approver"]

        labels = {
            "approver": "Do kogo chcesz wysłać prośbę o zatwierddzenie?*",
        }
        widgets = {
            "approver": Select(),
        }
