from django import forms

from .models import District, TeamRequest


class TeamRequestForm(forms.Form):
    patrols = forms.Field(widget=forms.HiddenInput(), required=False, label="Zastępy")

    user_patrol = forms.CharField(widget=forms.HiddenInput(), required=False)

    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        widget=forms.Select,
        label="Okręg",
        empty_label="Wybierz okręg",
    )

    team_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "np. 30 Zielonogórska Drużyna Harcerzy „Orlęta” im. Cichociemnych",
                "required": True,
            }
        ),
        label="Nazwa drużyny",
    )

    team_short_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "np. 30 ZDH",
                "maxlength": "10",
                "required": True,
            }
        ),
        label="Skrócona nazwa drużyny",
    )

    function_level = forms.ChoiceField(
        choices=TeamRequest.FUNCTION_CHOICES,
        initial=TeamRequest.FUNCTION_CHOICES[1][0],
        widget=forms.Select,
        label="Twoja funkcja",
    )

    class Meta:
        model = TeamRequest
        fields = ["district", "team_name", "team_short_name", "function_level"]
