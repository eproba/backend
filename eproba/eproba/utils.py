from drf_spectacular.utils import extend_schema
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
                "ads": False,
                "api_maintenance": True,
                "min_version": "20250500",
                "eol_date": "2025-09-30",
                "eol_screen_enabled": True,
                "eol_screen_title": "Nowa wersja Epróby jest już dostępna!",
                "eol_screen_description": "Ta wersja aplikacji zostaje wycofana. Aby korzystać z najnowszych funkcji i poprawek, pobierz nową wersję aplikacji.",
                "eol_screen_button_text": "Pobierz teraz",
                "eol_screen_button_url": "https://play.google.com/store/apps/details?id=pl.zhr.eproba.pwa",
            }
        )
