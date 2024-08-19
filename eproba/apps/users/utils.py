import json
from datetime import datetime
from functools import wraps
from uuid import UUID

from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def min_function(_min_function):
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.function >= _min_function:
                return function(request, *args, **kwargs)
            else:
                messages.error(
                    request, "Nie masz uprawnień do przeglądania tej strony."
                )
                return redirect(reverse("frontpage"))

        return wrap

    return decorator


def patrol_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.patrol:
            return function(request, *args, **kwargs)
        else:
            if request.user.is_authenticated:
                messages.error(request, "Nie jesteś przypisany do żadnej jednostki.")
                return redirect(reverse("frontpage"))
            else:
                messages.error(
                    request, "Musisz być zalogowany, aby przeglądać tę stronę."
                )
                return redirect(f"{reverse('login')}?next={request.path}")

    return wrap


def send_verification_email_to_user(user):

    name = (
        user.first_name
        if user.first_name
        else user.nickname if user.nickname else user.email
    )

    subject = "Weryfikacja adresu email"
    message = render_to_string(
        "users/email/verification_email.html",
        {
            "name": name,
            "verification_link": f"https://eproba.zhr.pl{reverse('verify_email', kwargs={'user_id': user.id, 'token': user.email_verification_token})}",
        },
    )
    send_mail(subject, strip_tags(message), None, [user.email], html_message=message)
