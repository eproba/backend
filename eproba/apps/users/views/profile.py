from allauth.socialaccount import signals as social_signals
from allauth.socialaccount.models import SocialAccount
from apps.users.models import User
from django.contrib import auth, messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.forms import TextInput
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.safestring import mark_safe


class UserChangeForm(auth.forms.UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ["nickname", "first_name", "last_name"]

        labels = {
            "nickname": "Pseudonim",
            "first_name": "Imię",
            "last_name": "Nazwisko",
        }
        widgets = {
            "nickname": TextInput(attrs={"class": "input"}),
            "first_name": TextInput(attrs={"class": "input"}),
            "last_name": TextInput(attrs={"class": "input"}),
        }


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
    user_id = request.user.id
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    if request.method == "POST":
        user_form = UserChangeForm(request.POST, instance=user)

        if user_form.is_valid():
            user = user_form.save()
            user.save()
            return redirect(
                reverse("frontpage")
                if request.GET.get("next") is None
                else request.GET.get("next")
            )

    else:
        user_form = UserChangeForm(instance=user)

    return render(
        request,
        "users/common.html",
        {"forms": [user_form], "info": "Dokończ konfigurowanie profilu"},
    )


@login_required
def check_signup_complete(request):
    if not request.user.patrol or not request.user.nickname:
        return redirect(reverse("finish_signup") + f"?next={request.GET.get('next')}")
    return redirect(request.GET.get("next", reverse("frontpage")))


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


@login_required
@transaction.atomic
def disconnect_socials(request, provider):
    user_id = request.user.id
    user = get_object_or_404(User, id=user_id)
    accounts = SocialAccount.objects.filter(user=user)
    for account in accounts:
        if account.provider == provider:
            if len(accounts) == 1 and not account.user.has_usable_password():
                messages.add_message(
                    request,
                    messages.INFO,
                    mark_safe(
                        f"Aby odłączyć konto społecznościowe musisz najpierw <a href='{reverse(set_password, kwargs={'user_id': user_id})}' >utworzyć hasło</a>."
                    ),
                )
                return redirect(reverse("view_profile", kwargs={"user_id": user_id}))
            account.delete()
            social_signals.social_account_removed.send(
                sender=SocialAccount, request=request, socialaccount=account
            )

    messages.add_message(
        request,
        messages.INFO,
        f"Konto {provider.capitalize()}™ zostało odłączone.",
    )
    return redirect(reverse("view_profile", kwargs={"user_id": user_id}))
