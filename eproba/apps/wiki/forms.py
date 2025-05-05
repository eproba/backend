# wiki/forms.py
from django import forms
from tinymce.widgets import TinyMCE

from .models import Page


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Wprowadź tytuł strony"}
            ),
            "content": TinyMCE(
                attrs={"class": "textarea", "placeholder": "Wprowadź treść strony"}
            ),
        }
