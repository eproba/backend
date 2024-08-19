import threading
import uuid

from apps.teams.models import District
from apps.users.forms import SiteUserCreationForm, TermsOfServiceForm
from apps.users.models import User
from apps.users.utils import send_verification_email_to_user
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.http import BadHeaderError, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from google.auth.transport import requests
from google.oauth2 import id_token


def signup(request):
    if request.method == "POST":
        user_form = SiteUserCreationForm(request.POST)
        terms_of_service_form = TermsOfServiceForm(request.POST)

        if user_form.is_valid() and terms_of_service_form.is_valid():
            user = user_form.save()
            send_email_thread = threading.Thread(
                target=send_verification_email_to_user, args=(user,), daemon=True
            )
            send_email_thread.start()
            login(request, user)
            if not user.patrol and request.GET.get("ignore_patrol") is None:
                return redirect(
                    f"{reverse('select_patrol')}?next={request.GET.get('next', reverse('worksheets:worksheets'))}"
                )
            return redirect(request.GET.get("next", reverse("worksheets:worksheets")))

    else:
        user_form = SiteUserCreationForm()
        terms_of_service_form = TermsOfServiceForm()
        user_form.fields["password1"].widget.attrs["class"] = "input"
        user_form.fields["password2"].widget.attrs["class"] = "input"

    return render(
        request,
        "users/signup.html",
        {"form": user_form, "terms_of_service_form": terms_of_service_form},
    )


@csrf_exempt
def google_auth_receiver(request):
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        return HttpResponse(status=501)
    if request.method != "POST":
        return HttpResponse(status=405)
    if "credential" not in request.POST:
        return HttpResponse(status=400)

    print("Inside")
    token = request.POST["credential"]

    try:
        user_data = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
            clock_skew_in_seconds=30,
        )
    except ValueError as e:
        return HttpResponse(e, status=400)

    user, created = User.objects.get_or_create(
        email=user_data["email"],
        defaults={
            "first_name": user_data.get("given_name", ""),
            "last_name": user_data.get("family_name", ""),
            "email_verified": True,
        },
    )

    if not user.email_verified:
        if user_data["email_verified"]:
            user.email_verified = True
            user.save()
        else:
            send_verification_email_to_user(user)

    login(request, user)

    next_url = request.GET.get("next", reverse("worksheets:worksheets"))

    if created:
        return redirect(f"{reverse('finish_signup')}?next={next_url}")

    return redirect(next_url)


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


def verify_email(request, user_id, token):
    user = get_object_or_404(User, id=user_id)
    if user.email_verification_token != token:
        messages.add_message(
            request, messages.ERROR, "Nieprawidłowy token weryfikacyjny."
        )
        return redirect(reverse("frontpage"))

    user.email_verified = True
    user.email_verification_token = (
        uuid.uuid4()
    )  # Invalidate the token and generate a new one for later use
    user.save()
    messages.add_message(request, messages.SUCCESS, "Adres email został zweryfikowany.")
    login(request, user)
    return redirect(reverse("frontpage"))


@login_required
def send_verification_email(request):
    if request.user.email_verified:
        messages.add_message(
            request, messages.INFO, "Twój adres email jest już zweryfikowany."
        )
        return redirect(reverse("frontpage"))
    try:
        send_verification_email_to_user(request.user)
    except Exception as e:
        messages.add_message(
            request,
            messages.ERROR,
            "Wystąpił błąd podczas wysyłania maila weryfikacyjnego.",
        )
        print(e)
        return redirect(reverse("frontpage"))

    messages.add_message(
        request,
        messages.SUCCESS,
        "Wysłaliśmy do ciebie maila z linkiem weryfikacyjnym.",
    )
    return redirect(request.GET.get("next", reverse("frontpage")))


@login_required
def select_patrol(request):
    if request.method == "POST":
        patrol_id = request.POST.get("patrol")
        if patrol_id:
            request.user.patrol_id = patrol_id
            request.user.save()
            messages.add_message(
                request, messages.SUCCESS, "Jednostka została wybrana."
            )
            return redirect(reverse("frontpage"))
        else:
            messages.add_message(
                request, messages.ERROR, "Jednostka nie została wybrana."
            )
            return redirect(reverse("select_patrol"))
    if request.user.patrol_id:
        return redirect(request.GET.get("next", reverse("frontpage")))

    districts = District.objects.all()

    return render(request, "users/select_patrol.html", {"districts": districts})
