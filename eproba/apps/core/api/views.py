from constance import config
from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import permissions, status
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from eproba import __version__ as eproba_version  # noqa: F401

from .serializers import ContactSerializer


class ContactAPIView(GenericAPIView):
    serializer_class = ContactSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            subject = serializer.validated_data["subject"]
            from_email = serializer.validated_data["from_email"]
            message = serializer.validated_data["message"]
            type_ = serializer.validated_data.get("type", "general")

            if type_ == "bug":
                subject = "[Zgłoszenie błędu] " + subject

            try:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=None,
                    to=["eproba@zhr.pl"],
                    headers={"Reply-To": from_email},
                )
                email.send()
                return Response(
                    {"message": "Wiadomość została wysłana."}, status=status.HTTP_200_OK
                )
            except Exception as e:
                raise APIException(str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        raise APIException(detail=serializer.errors, code=status.HTTP_400_BAD_REQUEST)


class ApiConfigView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response(
            {
                "maintenance": config.MAINTENANCE_MODE,
                "server_version": eproba_version,
                "api_version": settings.API_VERSION,
            }
        )
