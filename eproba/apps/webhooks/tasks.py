import hashlib
import hmac
import json
import logging
from functools import partial

import requests
from django.db import transaction
from django.tasks import task

from .models import Webhook

logger = logging.getLogger(__name__)


@task
def send_webhook(target_url, secret, event_type, payload):
    """
    Sends the payload to the target_url via webhook.
    Signs the request with HMAC SHA256 if secret is provided.
    """
    body = {"event": event_type, "data": payload}
    body_json = json.dumps(body)

    headers = {"Content-Type": "application/json", "User-Agent": "Eproba-Webhook/1.0"}

    if secret:
        signature = hmac.new(
            secret.encode("utf-8"), body_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        headers["X-Eproba-Signature"] = f"sha256={signature}"

    try:
        response = requests.post(
            target_url, data=body_json, headers=headers, timeout=10
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send webhook to {target_url}. Error: {e}")


def trigger_webhooks(event_type, target_user, payload):
    """
    Helper function to enqueue webhook tasks for a user's matched subscriptions.
    """

    webhooks = Webhook.objects.filter(user=target_user, is_active=True)

    for webhook in webhooks:
        if event_type in webhook.events:
            transaction.on_commit(
                partial(
                    send_webhook.enqueue,
                    target_url=webhook.url,
                    secret=webhook.secret,
                    event_type=event_type,
                    payload=payload,
                )
            )
