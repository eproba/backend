from apps.users.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import EmailInput, Select, TextInput
from django.utils.safestring import mark_safe


class SiteUserCreationForm(UserCreationForm):
    usable_password = None

    class Meta:
        model = User
        fields = (
            "email",
            "nickname",
            "first_name",
            "last_name",
            "patrol",
            "password1",
            "password2",
        )
        labels = {
            "nickname": "Pseudonim",
            "email": "Email",
            "first_name": "Imię",
            "last_name": "Nazwisko",
        }
        widgets = {
            "nickname": TextInput(attrs={"class": "input"}),
            "email": EmailInput(attrs={"class": "input"}),
            "first_name": TextInput(attrs={"class": "input"}),
            "last_name": TextInput(attrs={"class": "input"}),
            "patrol": Select(attrs={"class": "select"}),
        }


class TermsOfServiceForm(forms.Form):
    terms_of_service = forms.BooleanField(
        label=mark_safe(
            "Publikujemy Warunki korzystania z serwisu oraz Politykę prywatności, aby poinformować Cię, czego możesz się spodziewać, korzystając z naszych usług. Zaznaczając to polę, wyrażasz zgodę na te warunki."
        ),
        required=True,
    )
