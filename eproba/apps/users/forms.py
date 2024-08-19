from apps.users.models import User
from django import forms
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
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
            "gender",
            "password1",
            "password2",
        )
        labels = {
            "nickname": "Pseudonim",
            "email": "Email",
            "first_name": "Imię",
            "last_name": "Nazwisko",
            "gender": "Płeć",
        }


class TermsOfServiceForm(forms.Form):
    terms_of_service = forms.BooleanField(
        label=mark_safe(
            'Potwierdzam że zapoznałem się z <a href="/terms-of-service/" target="_blank">regulaminem</a> oraz <a href="/privacy-policy/" target="_blank">polityką prywatności</a> i akceptuję je.'
        ),
        required=True,
    )


class UserChangeForm(auth.forms.UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ["nickname", "first_name", "last_name", "gender"]

        labels = {
            "nickname": "Pseudonim",
            "first_name": "Imię",
            "last_name": "Nazwisko",
            "gender": "Płeć",
        }
