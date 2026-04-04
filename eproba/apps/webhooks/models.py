import secrets
import uuid

from apps.users.models import User
from django.db import models


def generate_secret():
    return secrets.token_hex(32)


class Webhook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webhooks")
    url = models.URLField(max_length=500, verbose_name="Webhook URL")
    secret = models.CharField(
        max_length=128,
        default=generate_secret,
        verbose_name="Secret for HMAC signature",
    )
    events = models.JSONField(default=list, verbose_name="Subscribed events")
    is_active = models.BooleanField(default=True, verbose_name="Is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.url)

    class Meta:
        verbose_name = "Webhook"
        verbose_name_plural = "Webhooks"
