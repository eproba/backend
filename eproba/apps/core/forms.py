from django import forms
from django.forms import EmailInput, Textarea, TextInput


class ContactForm(forms.Form):
    from_email = forms.EmailField(
        widget=EmailInput(),
        required=True,
        label="Twój email",
    )
    subject = forms.CharField(
        widget=TextInput(),
        required=True,
        label="Temat",
    )
    message = forms.CharField(
        widget=Textarea(),
        required=True,
        label="Wiadomość",
    )


class IssueContactForm(forms.Form):
    from_email = forms.EmailField(
        widget=EmailInput(),
        required=True,
        label="Twój email",
    )
    subject = forms.CharField(
        widget=TextInput(),
        required=True,
        label="Opisz problem w jednym zdaniu",
    )
    message = forms.CharField(
        widget=Textarea(),
        required=True,
        label="Opisz dokłądnie swój problem wraz z opisem jak na niego trafiłeś",
    )
