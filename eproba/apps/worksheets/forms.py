from apps.users.models import User
from apps.worksheets.models import Task, TemplateTask, TemplateWorksheet, Worksheet
from django import forms
from django.db.models import Q
from django.forms import ModelForm, Select, Textarea, TextInput


class WorksheetCreateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.template_notes = kwargs.pop("template_notes", None)
        super(WorksheetCreateForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Worksheet
        fields = ["name", "description"]
        labels = {
            "name": "Nazwa próby",
        }
        widgets = {
            "description": Textarea(attrs={"class": "textarea", "rows": 2}),
        }


class ExtendedWorksheetCreateForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        self.template_notes = kwargs.pop("template_notes", None)
        super(ExtendedWorksheetCreateForm, self).__init__(*args, **kwargs)
        self.fields["user"].required = True
        self.fields["user"].initial = user
        if user.patrol.team and user.function < 5:
            self.fields["user"].queryset = User.objects.filter(
                patrol__team=user.patrol.team
            )

    class Meta:
        model = Worksheet
        fields = ["user", "name", "description"]
        labels = {
            "user": "Dla kogo chcesz stworzyć próbę?",
            "name": "Nazwa próby",
        }
        widgets = {
            "description": Textarea(attrs={"class": "textarea", "rows": 2}),
        }


class TemplateWorksheetCreateForm(ModelForm):
    class Meta:
        model = TemplateWorksheet
        fields = ["name", "description", "template_notes"]
        labels = {
            "name": "Nazwa szablonu",
            "description": "Opis szablonu",
            "template_notes": "Notatki (widoczne tylko w szablonie)",
        }
        widgets = {
            "description": Textarea(attrs={"class": "textarea", "rows": 2}),
            "template_notes": Textarea(attrs={"class": "textarea", "rows": 2}),
        }


class ExtendedTemplateWorksheetCreateForm(ModelForm):
    for_organization = forms.BooleanField(
        label="Dla całej organizacji?",
        required=False,
        initial=False,
    )

    class Meta:
        model = TemplateWorksheet
        fields = ["name", "description", "template_notes", "for_organization"]
        labels = {
            "name": "Nazwa szablonu",
            "description": "Opis szablonu",
            "template_notes": "Notatki (widoczne tylko w szablonie)",
        }
        widgets = {
            "description": Textarea(attrs={"class": "textarea", "rows": 2}),
            "template_notes": Textarea(attrs={"class": "textarea", "rows": 2}),
        }


class TaskForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.template_notes = self.initial.get("template_notes")

    class Meta:
        model = Task
        fields = ["task", "description"]
        widgets = {
            "task": TextInput(attrs={"class": "input"}),
            "description": Textarea(attrs={"class": "textarea", "rows": 3}),
        }


class TemplateTaskForm(ModelForm):
    class Meta:
        model = TemplateTask
        fields = ["task", "description", "template_notes"]
        widgets = {
            "task": TextInput(attrs={"class": "input"}),
            "description": Textarea(attrs={"class": "textarea", "rows": 3}),
            "template_notes": Textarea(attrs={"class": "textarea", "rows": 3}),
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
