from apps.users.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import mixins, serializers, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from .permissions import IsAllowedToManageUserOrReadOnly
from .serializers import ChangePasswordSerializer, PublicUserSerializer, UserSerializer


class UserViewSet(
    mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated, IsAllowedToManageUserOrReadOnly]
    serializer_class = PublicUserSerializer

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
        # Example check for promotion restrictions
        data = serializer.validated_data
        if data and data.get("function", 0) > self.request.user.function:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Cannot assign a higher function than your own.")
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=kwargs["pk"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserInfo(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    ALLOWED_UPDATE_FIELDS = [
        "nickname",
        "first_name",
        "last_name",
        "email",
        "patrol",
        "is_active",
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
        if data.get("patrol", self.request.user.patrol) != self.request.user.patrol:
            if (
                not data.get("patrol")
                or not self.request.user.patrol
                or data["patrol"].team != self.request.user.patrol.team
            ):
                data["function"] = 0
            elif self.request.user.function <= 2:
                data["function"] = 0

        serializer.save()


class ChangePasswordView(APIView):
    """
    API view for changing user password.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

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
