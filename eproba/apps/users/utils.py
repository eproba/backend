import urllib.parse
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from fcm_django.admin import FCMDevice
from firebase_admin.messaging import (
    Message,
    WebpushConfig,
    WebpushFCMOptions,
    WebpushNotification,
)

from .models import User

logger = settings.LOGGER


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
    try:
        send_mail(
            subject, strip_tags(message), None, [user.email], html_message=message
        )
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")


def send_fcm_notification(targets: list[User], title: str, body: str, link: str):
    """Send FCM (Firebase Cloud Messaging) notification to users."""
    if settings.FIREBASE_APP is None:
        logger.warning("Firebase app is not initialized, notifications are disabled.")
        return
    try:
        FCMDevice.objects.filter(user__in=targets).send_message(
            Message(
                webpush=WebpushConfig(
                    notification=WebpushNotification(
                        title=title,
                        body=body,
                    ),
                    fcm_options=WebpushFCMOptions(
                        link=urllib.parse.urljoin("https://eproba.zhr.pl", link)
                    ),
                ),
            )
        )
    except Exception as e:
        logger.error(f"Error while sending FCM notification: {e}")
        pass


def send_email_notification(targets: list[User], subject: str, message: str, link: str):
    """Send email notification to users who have email notifications enabled."""

    # Filter users who have email notifications enabled
    enabled_users = [user for user in targets if user.email_notifications]

    if not enabled_users:
        return

    recipient_emails = [user.email for user in enabled_users]

    try:
        send_mail(
            subject,
            f"{message}\n\nLink: {link}",
            None,
            recipient_emails,
        )
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")


def send_notification(targets: list[User] | User, title: str, body: str, link: str):
    """Send both FCM and email notifications to users."""
    if not isinstance(targets, list):
        targets = [targets]

    send_fcm_notification(targets, title, body, link)
    send_email_notification(targets, title, body, link)
