import datetime

from constance import config
from constance.signals import config_updated
from django.dispatch import receiver
from drf_spectacular.utils import extend_schema
from maintenance_mode.core import set_maintenance_mode
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from eproba import __version__ as eproba_version  # noqa: F401


@extend_schema(deprecated=True)
class LegacyApiConfigView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response(
            {
                "ads": config.ADS_MOBILE,
                "api_maintenance": config.API_MAINTENANCE_MODE,
                "min_version": config.MINIMUM_APP_VERSION,
                "eol_date": datetime.date(2025, 8, 30).isoformat(),
                "eol_screen_enabled": config.EOL_SCREEN_ENABLED,
                "eol_screen_title": "Nowa wersja Epróby jest już dostępna!",
                "eol_screen_description": "Ta wersja aplikacji zostaje wycofana. Aby korzystać z najnowszych funkcji i poprawek, pobierz nową wersję aplikacji.",
                "eol_screen_button_text": "Pobierz nową wersję",
                "eol_screen_button_url": "https://dev-eproba.zhr.pl/", # test URL should be updated to the actual download link
            }
        )


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == "WEB_MAINTENANCE_MODE" and old_value != new_value:
        set_maintenance_mode(new_value)
