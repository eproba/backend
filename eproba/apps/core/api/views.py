from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializers import ContactSerializer


class ContactAPIView(GenericAPIView):
    serializer_class = ContactSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            subject = serializer.validated_data["subject"]
            from_email = serializer.validated_data["from_email"]
            message = serializer.validated_data["message"]

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
