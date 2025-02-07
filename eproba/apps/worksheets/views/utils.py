import urllib.parse

from apps.users.models import User
from django.conf import settings
from fcm_django.admin import FCMDevice
from firebase_admin.messaging import (
    Message,
    WebpushConfig,
    WebpushFCMOptions,
    WebpushNotification,
)

logger = settings.LOGGER


def prepare_worksheet(worksheet):
    _all = 0
    _done = 0
    worksheet.show_submit_task_button = False
    worksheet.show_sent_tasks_button = False
    worksheet.show_description_column = False
    for task in worksheet.tasks.all():
        _all += 1
        if task.status == 2:
            _done += 1
        elif task.status in [0, 3]:
            worksheet.show_submit_task_button = True
        elif task.status == 1:
            worksheet.show_sent_tasks_button = True
        if task.description != "":
            worksheet.show_description_column = True
    if _all != 0:
        percent = int(round(_done / _all, 2) * 100)
        worksheet.percent = f"{percent}%"
    else:
        worksheet.percent = "Nie masz jeszcze dodanych żadnych zadań"

    return worksheet


def send_notification(targets: list[User] | User, title: str, body: str, link: str):
    if settings.FIREBASE_APP is None:
        logger.warning("Firebase app is not initialized, notifications are disabled.")
        return
    if not isinstance(targets, list):
        targets = [targets]
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
        logger.error(f"Error while sending notification: {e}")
        pass
