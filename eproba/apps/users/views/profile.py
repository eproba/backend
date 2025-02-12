from urllib.parse import urlencode

from apps.teams.models import Patrol
from apps.users.forms import UserChangeForm
from apps.users.models import User
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
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
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.method == "POST":
        user_form = UserChangeForm(request.POST, instance=user)

        if user_form.is_valid():
            user = user_form.save()
            user.save()
            return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    else:
        user_form = UserChangeForm(instance=user)

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

        if user_form.is_valid():
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
        user_form = UserChangeForm(instance=request.user)

    return render(
        request,
        "users/common.html",
        {
            "forms": [user_form],
            "info": "Dokończ konfigurowanie profilu",
            "button_text": "Dalej",
        },
    )


@login_required
@transaction.atomic
def set_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.user.has_usable_password():
        return redirect(reverse("change_password", kwargs={"user_id": user_id}))

    if request.method == "POST":
        password_form = SetPasswordForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.add_message(request, messages.SUCCESS, "Hasło zostało zmienione.")
            return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    else:
        password_form = SetPasswordForm(request.user)
        password_form.fields["new_password1"].widget.attrs["class"] = "input"
        password_form.fields["new_password2"].widget.attrs["class"] = "input"

    return render(
        request, "users/common.html", {"forms": [password_form], "info": "Utwórz hasło"}
    )
