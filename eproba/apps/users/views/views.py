from apps.users.forms import SiteUserCreationForm
from apps.users.models import User
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.db import transaction
from django.http import BadHeaderError, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse


@transaction.atomic
def signup(request):
    if request.method == "POST":
        user_form = SiteUserCreationForm(request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.refresh_from_db()
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect(
                "frontpage"
                if request.GET.get("next") is None
                else request.GET.get("next")
            )

    else:
        user_form = SiteUserCreationForm()
        # terms_of_service_form = TermsOfServiceForm()
        user_form.fields["password1"].widget.attrs["class"] = "input"
        user_form.fields["password2"].widget.attrs["class"] = "input"

    return render(
        request,
        "users/signup.html",
        {"form": user_form, "info": "Załóż konto"},
    )


def password_reset_done(request):
    messages.add_message(
        request,
        messages.SUCCESS,
        "Wysłaliśmy do ciebie maila z linkiem do zresetowania hasła, jeśli go nie otrzymałeś odczekaj kilka sekund, sprawdź kosz i spam. Jeśli nadal nie możesz go znaleźć, spróbuj ponownie zresetować hasło uważając na poprawność adresu email.",
    )
    return redirect(reverse("login"))


def password_reset_complete(request):
    messages.add_message(
        request,
        messages.SUCCESS,
        "Hasło zostało zresetowane i możesz się już zalogować.",
    )
    return redirect(reverse("login"))


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
            messages.add_message(request, messages.SUCCESS, "Hasło zostało zmienione.")
            return redirect(reverse("view_profile", kwargs={"user_id": user_id}))

    else:
        password_form = PasswordChangeForm(request.user)
        password_form.fields["old_password"].widget.attrs["class"] = "input"
        password_form.fields["new_password1"].widget.attrs["class"] = "input"
        password_form.fields["new_password2"].widget.attrs["class"] = "input"

    return render(
        request, "users/common.html", {"forms": [password_form], "info": "Zmień hasło"}
    )


def duplicated_accounts(request, user_id_1, user_id_2):
    user_1 = get_object_or_404(User, id=user_id_1)
    user_2 = get_object_or_404(User, id=user_id_2)

    if user_1 == user_2:
        messages.add_message(
            request, messages.ERROR, "Nie możesz porównać dwóch takich samych kont."
        )
        return redirect(reverse("frontpage"))

    if request.user != user_1 and request.user != user_2:
        messages.add_message(
            request, messages.ERROR, "Nie masz uprawnień do przeglądania tej strony."
        )
        return redirect(reverse("frontpage"))

    if request.method == "POST":
        selected_user = get_object_or_404(User, id=request.POST.get("selected_user"))
        note = request.POST.get("note")

        try:
            send_mail(
                "Zgłoszenie zduplikowanych kont",
                f"Zgłoszenie zduplikowanych kont od {request.user.email}.\n\nKonto 1: {user_1.email}\nKonto 2: {user_2.email}\n\nWybrane konto: {selected_user.email} (ID: {selected_user.id})\n\nNotatka: {note}",
                None,
                ["antoni.czaplicki@zhr.pl"],
            )
        except BadHeaderError:
            return HttpResponse("Invalid header found.")
        messages.add_message(
            request,
            messages.INFO,
            "Zgłoszenie zostało wysłane, w ciągu kilku dni twoje stare konto zostanie usunięte.",
        )
        return redirect(reverse("frontpage"))

    return render(
        request, "users/duplicated_accounts.html", {"user_1": user_1, "user_2": user_2}
    )
