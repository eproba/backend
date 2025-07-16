import threading
import uuid
from urllib.parse import urlencode

from apps.teams.models import District, Patrol
from apps.users.forms import SiteUserCreationForm, TermsOfServiceForm
from apps.users.models import User
from apps.users.utils import send_verification_email_to_user
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from google.auth.transport import requests
from google.oauth2 import id_token


def signup(request):
    query_params = request.GET.dict()
    if request.user.is_authenticated:
        if not request.user.patrol and query_params.get("patrol"):
            request.user.patrol = Patrol.objects.get(id=query_params.get("patrol"))
            query_params.pop("patrol", None)
            request.user.save()
        if request.GET.get("finish_signup") == "true":
            next_url = query_params.get("next", reverse("worksheets:worksheets"))
            query_params["next"] = next_url
            query_params.pop("finish_signup", None)
            return redirect(
                f"{reverse('finish_signup')}?{urlencode(query_params, doseq=True)}"
            )
        return redirect(request.GET.get("next", reverse("worksheets:worksheets")))
    if request.method == "POST":
        user_form = SiteUserCreationForm(request.POST)
        terms_of_service_form = TermsOfServiceForm(request.POST)

        if user_form.is_valid() and terms_of_service_form.is_valid():
            user = user_form.save()
            patrol_id = query_params.pop("patrol", None)
            if patrol_id:
                patrol = Patrol.objects.get(id=patrol_id)
                if patrol:
                    user.patrol = patrol
                    user.save()
            send_email_thread = threading.Thread(
                target=send_verification_email_to_user, args=(user,), daemon=True
            )
            send_email_thread.start()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            if not user.patrol and request.GET.get("ignore_patrol") is None:
                return redirect(
                    f"{reverse('select_patrol')}?{urlencode(request.GET, doseq=True)}"
                )
            return redirect(request.GET.get("next", reverse("worksheets:worksheets")))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                f"Wystąpił błąd podczas rejestracji użytkownika: {user_form.errors.as_text()}",
            )

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

    token = request.POST["credential"]
    state = request.POST.get("state", "")

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

    if user.is_deleted:
        messages.add_message(
            request, messages.ERROR, "Konto jest usunięte, nie możesz się zalogować."
        )
        return redirect(reverse("frontpage"))

    if not user.email_verified:
        if user_data["email_verified"]:
            user.email_verified = True
            user.save()
        else:
            send_verification_email_to_user(user)

    if not created:
        if not user.first_name:
            user.first_name = user_data.get("given_name", "")
        if not user.last_name:
            user.last_name = user_data.get("family_name", "")

    if not user.is_active:
        messages.add_message(
            request,
            messages.ERROR,
            "Konto jest dezaktywowane, nie możesz się zalogować.",
        )

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    if created:
        return redirect(
            f"{reverse('signup')}?{urlencode({'next': state, 'finish_signup': 'true'})}"
        )
    return redirect(state or reverse("frontpage"))


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
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
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
            return redirect(request.GET.get("next", reverse("frontpage")))
        else:
            messages.add_message(
                request, messages.ERROR, "Jednostka nie została wybrana."
            )
            return redirect(reverse("select_patrol"))
    if request.user.patrol_id:
        return redirect(request.GET.get("next", reverse("frontpage")))

    districts = District.objects.all()

    return render(request, "users/select_patrol.html", {"districts": districts})
