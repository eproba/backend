from apps.users.models import User
from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsAllowedToManageUserOrReadOnly
from .serializers import PublicUserSerializer, UserSerializer


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
        data = serializer.validated_data.get("user")
        if data and data.get("function", 0) > self.request.user.function:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Cannot assign a higher function than your own.")
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=kwargs["pk"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserInfo(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(request.user).data)
