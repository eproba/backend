from apps.teams.models import Patrol
from apps.users.models import Scout, User
from django import forms
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (
    PasswordChangeForm,
    SetPasswordForm,
    UserChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import Group
from django.db import transaction
from django.forms import Select
from django.shortcuts import get_object_or_404, redirect, render, reverse


class SiteUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "nickname"]
        labels = {"nickname": "Pseudonim", "email": "Email"}


class ScoutCreationForm(forms.ModelForm):
    class Meta:
        model = Scout
        fields = ["patrol"]

        labels = {"patrol": "Zastęp"}
        widgets = {
            "patrol": Select(),
        }


@transaction.atomic
def signup(request):
    if request.method == "POST":
        user_form = SiteUserCreationForm(request.POST)
        scout_form = ScoutCreationForm(request.POST)

        if user_form.is_valid() and scout_form.is_valid():
            user = user_form.save()
            user.refresh_from_db()
            user.scout.patrol = scout_form.cleaned_data.get("patrol")
            user.scout.team = user.scout.patrol.team
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("frontpage")

    else:
        user_form = SiteUserCreationForm()
        scout_form = ScoutCreationForm()

    return render(
        request,
        "users/signup.html",
        {"forms": [user_form, scout_form], "info": "Załóż konto"},
    )


def view_profile(request, user_id):
    user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    return render(
        request,
        "users/view_profile.html",
        {"user": user, "allow_edit": bool(user == request.user)},
    )


class UserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ["nickname"]

        labels = {"nickname": "Pseudonim"}


class ScoutChangeForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(ScoutChangeForm, self).__init__(*args, **kwargs)
        if request.user.scout.team:
            self.fields["patrol"].queryset = Patrol.objects.filter(
                team=request.user.scout.team
            )
        else:
            self.fields["patrol"].queryset = Patrol.objects

    class Meta:
        model = Scout
        fields = ["patrol"]

        labels = {
            "patrol": "Zastęp",
        }
        widgets = {
            "patrol": Select(),
        }


def password_reset_done(request):
    messages.add_message(
        request,
        messages.SUCCESS,
        "Wysłaliśmy do ciebie maila z linkiem do zresetowania hasła, jeśli go nie otrzymałeś odczekaj kilka sekund, sprawdź kosz i spam. Jeśli nadal nie możesz go znaleźć, spróbuj ponownie zresetować hasło uważając na poprawność adresu email.",
    )
    return redirect(reverse("frontpage"))


def password_reset_complete(request):
    messages.add_message(
        request,
        messages.SUCCESS,
        "Hasło zostało zresetowane i możesz się już zalogować.",
    )
    return redirect(reverse("login"))


@login_required
@transaction.atomic
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.method == "POST":
        user_form = UserChangeForm(request.POST, instance=user)
        scout_form = ScoutChangeForm(request, request.POST, instance=user.scout)

        if user_form.is_valid() and scout_form.is_valid():
            user = user_form.save()
            user.scout.patrol = scout_form.cleaned_data.get("patrol")
            user.scout.team = user.scout.patrol.team
            user.save()
            return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    else:
        user_form = UserChangeForm(instance=user)
        scout_form = ScoutChangeForm(request=request, instance=user.scout)

    return render(
        request,
        "users/common.html",
        {"forms": [user_form, scout_form], "info": "Edytuj profil"},
    )


@login_required
@transaction.atomic
def change_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.method == "POST":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    else:
        password_form = PasswordChangeForm(request.user)

    return render(
        request, "users/common.html", {"forms": [password_form], "info": "Zmień hasło"}
    )


@login_required
@transaction.atomic
def set_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.method == "POST":
        password_form = SetPasswordForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    else:
        password_form = SetPasswordForm(request.user)

    return render(
        request, "users/common.html", {"forms": [password_form], "info": "Utwórz hasło"}
    )


@login_required
@transaction.atomic
def finish_signup(request):
    user_id = request.user.id
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.method == "POST":
        user_form = UserChangeForm(request.POST, instance=user)
        scout_form = ScoutChangeForm(request, request.POST, instance=user.scout)

        if user_form.is_valid() and scout_form.is_valid():
            user = user_form.save()
            user.scout.patrol = scout_form.cleaned_data.get("patrol")
            user.scout.team = user.scout.patrol.team
            user.save()
            return redirect(reverse("frontpage"))

    else:
        user_form = UserChangeForm(instance=user)
        scout_form = ScoutChangeForm(request=request, instance=user.scout)

    return render(
        request,
        "users/common.html",
        {"forms": [user_form, scout_form], "info": "Dokończ konfigurowanie profilu"},
    )


@login_required
@transaction.atomic
def disconect_socials(request):
    user_id = request.user.id
    user = get_object_or_404(User, id=user_id)
    messages.add_message(
        request,
        messages.INFO,
        "Aby odłączyć konto społecznościowe skontaktuj się z administratorem.",
    )
    return redirect(reverse("view_profile", kwargs={"user_id": user_id}))
