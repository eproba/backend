from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apps.webhooks"
    verbose_name = "Webhooks"

    def ready(self):
        import apps.webhooks.signals  # noqa
