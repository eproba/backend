import uuid

from apps.users.models import User
from apps.users.utils import send_notification, send_verification_email_to_user
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q, Value
from django.db.models.functions import Concat
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from .permissions import IsAllowedToManageUserOrReadOnly
from .serializers import (
    ChangePasswordSerializer,
    PublicUserSerializer,
    ResendEmailVerificationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class UserViewSet(
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, IsAllowedToManageUserOrReadOnly]

    def get_serializer_class(self):
        if self.request.user.function >= 3:
            return UserSerializer
        return PublicUserSerializer

    def get_queryset(self):
        # Check if a list of IDs is provided in the query string
        ids = self.request.query_params.get("ids")
        if ids:
            # Expect a comma-separated list of IDs (UUIDs)
            user_ids = [uid.strip() for uid in ids.split(",") if uid.strip()]
            return User.objects.filter(id__in=user_ids)

        team_id = self.request.query_params.get("team")
        if team_id is not None:
            return User.objects.filter(patrol__team_id=team_id)

        if self.request.user.patrol is None:
            return User.objects.none()

        return User.objects.filter(patrol__team_id=self.request.user.patrol.team.id)

    def perform_update(self, serializer):
        data = serializer.validated_data
        if data.get("email") and data["email"] != self.request.user.email:
            self.request.user.email_verified = False
        serializer.save()

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search users by nickname, email, first name, or last name.
        """
        query = request.query_params.get("q", "")
        search_outside_team = (
            request.query_params.get("outside_team", "false").lower() == "true"
        )
        if not query:
            return Response(
                {"detail": "Query parameter 'q' is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        if not len(query.strip()) >= 3:
            return Response(
                {"detail": "Query parameter 'q' must be at least 3 characters long."},
                status=HTTP_400_BAD_REQUEST,
            )

        users = User.objects.annotate(
            _full_name=Concat(
                "first_name", Value(" "), "last_name", Value(" "), "nickname"
            )
        ).filter(
            Q(nickname__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(_full_name__icontains=query)
        )
        if not search_outside_team:
            users = users.filter(patrol__team=self.request.user.patrol.team)

        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)


class CurrentUserViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    """
    API view for managing the current authenticated user.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    ALLOWED_UPDATE_FIELDS = [
        "nickname",
        "first_name",
        "last_name",
        "email",
        "patrol",
        "is_active",
        "email_notifications",
    ]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        data = serializer.validated_data
        for field in data.keys():
            if field not in self.ALLOWED_UPDATE_FIELDS:
                raise serializers.ValidationError(
                    f"Field '{field}' is not allowed to be updated."
                )
        if data.get("email") and data["email"] != self.request.user.email:
            self.request.user.email_verified = False
            self.request.user.email_verification_token = uuid.uuid4()
            send_verification_email_to_user(self.request.user)
        new_patrol = data.get("patrol")
        if new_patrol and new_patrol != self.request.user.patrol:
            if (
                not new_patrol
                or not self.request.user.patrol
                or new_patrol.team != self.request.user.patrol.team
            ):
                data["function"] = 0
                if new_patrol:
                    send_notification(
                        User.objects.filter(
                            Q(patrol__team=new_patrol.team) & Q(function=4)
                        ),
                        f"{self.request.user.full_name_nickname()} dołączył do twojej drużyny",
                        f"{self.request.user.full_name_nickname()} dołączył do zastępu {new_patrol.name} w twojej drużynie.",
                        f"team?highlightedUserId={self.request.user.id}",
                    )
            elif self.request.user.function <= 2:
                data["function"] = 0

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.is_deleted = True
        user.is_staff = False
        user.is_superuser = False
        user.set_unusable_password()
        user.email = f"deleted-{uuid.uuid4()}-{user.email}"
        user.save()
        return Response(
            {"detail": "User account has been deleted."}, status=HTTP_200_OK
        )


class ChangePasswordView(GenericAPIView):
    """
    API view for changing user password.
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            try:
                validate_password(serializer.validated_data["new_password"], user)
            except ValidationError as e:
                return Response(
                    {"new_password": e.messages}, status=HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response(
                {"detail": "Password successfully changed"}, status=HTTP_200_OK
            )

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(GenericAPIView):
    """
    API view for resending email verification to authenticated user.
    """

    serializer_class = ResendEmailVerificationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        user = request.user

        if user.email_verified:
            return Response(
                {"detail": "Email is already verified"}, status=HTTP_400_BAD_REQUEST
            )

        try:
            send_verification_email_to_user(user)
            return Response(
                {"detail": "Verification email sent successfully"}, status=HTTP_200_OK
            )
        except Exception as e:
            raise APIException({"detail": str(e)}, code=HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyEmailView(GenericAPIView):
    """
    API view for verifying email with token.
    """

    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]

        user.email_verified = True
        user.email_verification_token = (
            uuid.uuid4()
        )  # Generate new token to invalidate old one
        user.save()

        return Response({"detail": "Email verified successfully"}, status=HTTP_200_OK)
