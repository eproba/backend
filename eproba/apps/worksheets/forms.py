from django import forms
from django.db.models import Q
from django.forms import ModelForm, Select, TextInput

from ..users.models import User
from .models import Task, Worksheet


class WorksheetCreateForm(ModelForm):
    class Meta:
        model = Worksheet
        fields = ["name"]
        labels = {
            "name": "Nazwa próby",
        }


class ExtendedWorksheetCreateForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ExtendedWorksheetCreateForm, self).__init__(*args, **kwargs)
        self.fields["user"].required = True
        self.initial["user"] = user
        if user.patrol.team and user.function < 5:
            self.fields["user"].queryset = User.objects.filter(
                patrol__team=user.patrol.team
            )

    class Meta:
        model = Worksheet
        fields = ["user", "name"]
        labels = {
            "user": "Dla kogo chcesz stworzyć próbę?",
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


class SubmitTaskForm(ModelForm):
    def __init__(self, request, worksheet, *args, **kwargs):
        super(SubmitTaskForm, self).__init__(*args, **kwargs)
        if request.user.patrol:
            query = Q(function__gte=2)
            query.add(Q(function__gt=request.user.function), Q.AND)
            query.add(Q(patrol__team=request.user.patrol.team), Q.AND)
            self.fields["approver"].queryset = User.objects.filter(query).exclude(
                id=request.user.id
            )
        else:
            self.fields["approver"].queryset = User.objects.filter(
                Q(function__gte=2)
            ).exclude(id=request.user.id)
        self.fields["task"].queryset = (
            Task.objects.filter(worksheet=worksheet).exclude(status=1).exclude(status=2)
        )
        self.fields["task"].widget.attrs["class"] = "select form-control"

    task = forms.ModelChoiceField(queryset=None, label="Wybierz zadanie do przesłania")

    class Meta:
        model = Task
        fields = ["task", "approver"]

        labels = {
            "approver": "Do kogo chcesz wysłać prośbę o zatwierdzenie?*",
        }
        widgets = {
            "approver": Select(
                attrs={
                    "class": "select form-control",
                    "required": "required",
                }
            ),
        }
