from apps.users.models import User
from django import forms
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.utils.safestring import mark_safe


class SiteUserCreationForm(UserCreationForm):
    usable_password = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = (
            "Hasło musi mieć co najmniej 8 znaków i być chociaż w miarę silne."
        )

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
        help_texts = {
            "email": "Jeśli posiadasz to skorzystaj z adresu email w domenie @zhr.pl",
        }


class TermsOfServiceForm(forms.Form):
    terms_of_service = forms.BooleanField(
        label=mark_safe(
            'Potwierdzam że zapoznałem się z <a href="/terms-of-service/" target="_blank">regulaminem</a> oraz <a href="/privacy-policy/" target="_blank">polityką prywatności</a> i akceptuję je.'
        ),
        required=True,
    )
    personal_data_processing = forms.BooleanField(
        label=mark_safe(
            "Wyrażam zgodę na przetwarzanie danych osobowych w celach związanych z rejestracją i obsługą konta w serwisie. Rozumiem, że zgoda może być wycofana w dowolnym momencie i nie wpłynie to na przetwarzanie, którego dokonano przed jej wycofaniem"
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
