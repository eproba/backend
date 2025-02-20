import uuid
from urllib.parse import urlencode

from apps.teams.models import Patrol
from apps.users.forms import TermsOfServiceForm, UserChangeForm
from apps.users.models import User
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse


def view_profile(request, user_id):
    user = request.user if user_id is None else get_object_or_404(User, id=user_id)
    if user_id is None and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    return render(
        request,
        "users/view_profile.html",
        {"user": user, "allow_edit": user == request.user},
    )


@login_required
@transaction.atomic
def edit_profile(request):
    if request.method == "POST":
        user_form = UserChangeForm(request.POST, instance=request.user)

        if user_form.is_valid():
            user = user_form.save()
            user.save()
            return redirect(reverse("view_profile"))

    else:
        user_form = UserChangeForm(instance=request.user)

    return render(
        request,
        "users/common.html",
        {"forms": [user_form], "info": "Edytuj profil"},
    )


@login_required
@transaction.atomic
def finish_signup(request):
    if request.method == "POST":
        user_form = UserChangeForm(request.POST, instance=request.user)
        terms_of_service_form = TermsOfServiceForm(request.POST)

        if user_form.is_valid() and terms_of_service_form.is_valid():
            user = user_form.save()
            user.save()
            query_params = request.GET.dict()
            patrol_id = query_params.pop("patrol", None)
            if patrol_id:
                patrol = Patrol.objects.get(id=patrol_id)
                if patrol:
                    user.patrol = patrol
                    user.save()
            if not user.patrol and request.GET.get("ignore_patrol") is None:
                return redirect(f"{reverse('select_patrol')}?{urlencode(query_params)}")
            return redirect(request.GET.get("next", reverse("worksheets:worksheets")))
        else:
            messages.add_message(request, messages.ERROR, "Wystąpił błąd.")

    user_form = UserChangeForm(instance=request.user)
    terms_of_service_form = TermsOfServiceForm()

    return render(
        request,
        "users/common.html",
        {
            "forms": [user_form, terms_of_service_form],
            "info": "Dokończ konfigurowanie profilu",
            "button_text": "Dalej",
        },
    )


@login_required
@transaction.atomic
def set_password(request):
    if request.user.has_usable_password():
        return redirect(reverse("change_password"))

    if request.method == "POST":
        password_form = SetPasswordForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.add_message(request, messages.SUCCESS, "Hasło zostało zmienione.")
            return redirect(reverse("view_profile"))

    else:
        password_form = SetPasswordForm(request.user)
        password_form.fields["new_password1"].widget.attrs["class"] = "input"
        password_form.fields["new_password2"].widget.attrs["class"] = "input"

    return render(
        request, "users/common.html", {"forms": [password_form], "info": "Utwórz hasło"}
    )


@login_required
def change_password(request):
    if request.method == "POST":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.add_message(request, messages.SUCCESS, "Hasło zostało zmienione.")
            return redirect(reverse("view_profile"))

    else:
        password_form = PasswordChangeForm(request.user)
        password_form.fields["old_password"].widget.attrs["class"] = "input"
        password_form.fields["new_password1"].widget.attrs["class"] = "input"
        password_form.fields["new_password2"].widget.attrs["class"] = "input"

    return render(
        request, "users/common.html", {"forms": [password_form], "info": "Zmień hasło"}
    )


@login_required
def delete_account(request):
    if request.method == "POST":
        if request.POST.get("confirmation") != "USUŃ KONTO":
            messages.add_message(request, messages.ERROR, "Niepoprawne potwierdzenie.")
            return render(request, "users/delete_account.html")
        request.user.set_unusable_password()
        request.user.is_active = False
        request.user.is_deleted = True
        request.user.email = f"deleted-{uuid.uuid4()}-{request.user.email}"
        request.user.save()
        messages.add_message(request, messages.INFO, "Konto zostało usunięte.")
        return redirect(reverse("frontpage"))

    return render(request, "users/delete_account.html")
