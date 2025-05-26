from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "apps.users"
    verbose_name = "Użytkownicy"

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals
