from datetime import datetime

from apps.teams.models import Patrol, Team
from apps.teams.permissions import (
    IsAllowedToManagePatrolOrReadOnly,
    IsAllowedToManageTeamOrReadOnly,
)
from apps.teams.serializers import PatrolSerializer, TeamSerializer
from apps.users.models import User
from apps.users.permissions import IsAllowedToManageUserOrReadOnly
from apps.users.serializers import PublicUserSerializer, UserSerializer
from apps.users.tasks import clear_tokens
from apps.worksheets.models import Task, Worksheet
from apps.worksheets.permissions import (
    IsAllowedToManageTaskOrReadOnlyForOwner,
    IsAllowedToManageWorksheetOrReadOnlyForOwner,
    IsTaskOwner,
)
from apps.worksheets.serializers import TaskSerializer, WorksheetSerializer
from apps.worksheets.tasks import remove_expired_deleted_worksheets
from constance import config
from constance.signals import config_updated
from django.db.models import Q
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from fcm_django.models import FCMDevice
from firebase_admin.messaging import (
    Message,
    Notification,
    WebpushConfig,
    WebpushFCMOptions,
)
from maintenance_mode.core import set_maintenance_mode
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet


class AppConfigView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response(
            {
                "ads": config.ADS_MOBILE,
                "maintenance": True,  # this id for backwards compatibility
                "api_maintenance": config.API_MAINTENANCE_MODE,
                "min_version": config.MINIMUM_APP_VERSION,
            }
        )


class UserViewSet(
    mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = PublicUserSerializer
    permission_classes = (IsAuthenticated, IsAllowedToManageUserOrReadOnly)

    def get_queryset(self):
        if self.request.query_params.get("team") is not None:
            return User.objects.filter(
                patrol__team_id=self.request.query_params.get("team")
            )
        if self.request.user.patrol is None:
            return User.objects.none()
        return User.objects.filter(
            Q(patrol__team_id=self.request.user.patrol.team.id)
            | Q(patrol__isnull=True, is_active=False)
        )

    def perform_update(self, serializer):
        if serializer.validated_data.get("user") is not None:
            user = serializer.validated_data.get("user")
            if user.get("function") is not None:
                if user.get("function") > self.request.user.function:
                    raise PermissionDenied()
        if (
            serializer.instance.is_active is False
            and serializer.validated_data.get("is_active") is True
            and serializer.instance.patrol is None
            and self.request.user.patrol
        ):
            try:
                serializer.validated_data["user"]["patrol"] = self.request.user.patrol
            except KeyError:
                serializer.validated_data["user"] = {"patrol": self.request.user.patrol}
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=kwargs["pk"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserInfo(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(request.user).data)


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = (IsAllowedToManageTeamOrReadOnly,)
    queryset = Team.objects.all()


class PatrolViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
    mixins.DestroyModelMixin,
):
    serializer_class = PatrolSerializer
    permission_classes = (IsAllowedToManagePatrolOrReadOnly,)
    queryset = Patrol.objects.all()

    def perform_destroy(self, instance):
        if instance.users.count() > 0:
            if instance.users.filter(user__is_active=True).count() > 0:
                exception = APIException("Patrol has users")
                exception.status_code = 409
                raise exception
            if instance.team.patrol_set.count() > 1:
                for user in instance.users.all():
                    user.patrol = instance.team.patrol_set.exclude(
                        id=instance.id
                    ).first()
                    user.save()
            else:
                for user in instance.users.all():
                    user.patrol = None
                    user.function = 0
                    user.save()
        instance.delete()

    def perform_create(self, serializer):
        if self.request.user.function <= 2:
            raise PermissionDenied()
        if self.request.user.function in [3, 4]:
            if serializer.validated_data.get("team") is not None:
                if (
                    serializer.validated_data.get("team").id
                    != self.request.user.patrol.team.id
                ):
                    raise PermissionDenied()
                serializer.save()
            serializer.validated_data["team"] = self.request.user.patrol.team
        serializer.save()


class TasksToBeChecked(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorksheetSerializer

    def get_queryset(self):
        return Worksheet.objects.filter(
            tasks__approver=self.request.user, tasks__status=1
        ).distinct()


class TaskDetails(ModelViewSet):
    permission_classes = [
        IsAllowedToManageTaskOrReadOnlyForOwner,
        permissions.IsAuthenticated,
    ]
    serializer_class = TaskSerializer
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        task = get_object_or_404(self.get_queryset(), id=kwargs["id"])
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    def get_queryset(self):
        if self.request.user.function >= 5:
            return Task.objects.filter(
                worksheet__id=self.kwargs["worksheet_id"]
            ).filter(id=self.kwargs["id"])
        if self.request.user.patrol and self.request.user.function >= 2:
            return Task.objects.filter(
                Q(id=self.kwargs["id"])
                & Q(worksheet__id=self.kwargs["worksheet_id"])
                & Q(
                    worksheet__patrol__team__id=self.request.user.patrol.team.id,
                    worksheet__is_template=False,
                    worksheet__is_archived=False,
                )
                | Q(
                    worksheet__supervisor__id=self.request.user.id,
                    worksheet__is_template=False,
                    worksheet__is_archived=False,
                )
            )

        return Task.objects.filter(
            worksheet__id=self.kwargs["worksheet_id"],
            worksheet__user__id=self.request.user.id,
        ).filter(id=self.kwargs["id"])

    def perform_update(self, serializer):
        super().perform_update(serializer)
        serializer.instance.worksheet.save()  # update worksheets modification date
        clear_tokens()  # clear old oauth2 tokens


class SubmitTask(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTaskOwner]

    def post(self, request, *args, **kwargs):
        if request.data.get("approver") is None:
            return Response({"approver": "This field is required."}, status=422)
        task = get_object_or_404(
            Task, id=kwargs["id"], worksheet__id=kwargs["worksheet_id"]
        )
        if task.status == 2:
            return Response({"message": "Task already approved"})
        task.status = 1
        task.approver = User.objects.get(user_id=request.data["approver"])
        task.approval_date = timezone.now()
        task.save()
        FCMDevice.objects.filter(user=task.approver).send_message(
            Message(
                notification=Notification(
                    title="Nowe zadanie do sprawdzenia",
                    body=f"Pojawił się nowy punkt do sprawdzenia dla {task.worksheet.user}.",
                ),
                webpush=WebpushConfig(
                    fcm_options=WebpushFCMOptions(
                        link="https://"
                        + request.get_host()
                        + reverse("worksheets:check_tasks")
                    ),
                ),
            )
        )
        return Response({"message": "Task submitted"})


class UnsubmitTask(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTaskOwner]

    def post(self, request, *args, **kwargs):
        task = get_object_or_404(
            Task, id=kwargs["id"], worksheet__id=kwargs["worksheet_id"]
        )
        if task.status != 1:
            return Response({"message": "Task is not submitted"})
        task.status = 0
        task.approver = None
        task.approval_date = None
        task.save()
        return Response({"message": "Task unsubmitted"})


class WorksheetViewSet(ModelViewSet):
    permission_classes = [IsAllowedToManageWorksheetOrReadOnlyForOwner, IsAuthenticated]
    serializer_class = WorksheetSerializer

    def get_object(self):
        return get_object_or_404(Worksheet, id=self.kwargs[self.lookup_field])

    def get_queryset(self):
        last_sync = self.request.query_params.get("last_sync")
        if last_sync is not None:
            worksheets = Worksheet.objects.filter(
                updated_at__gt=datetime.fromtimestamp(int(last_sync))
            )
        else:
            worksheets = Worksheet.objects.all()
        user = self.request.user
        if self.request.query_params.get("user") is not None:
            return worksheets.filter(
                user__id=user.id, is_template=False, is_archived=False
            )
        if self.request.query_params.get("templates") is not None:
            return worksheets.filter(
                user__patrol__team__id=user.patrol.team.id,
                is_template=True,
                is_archived=False,
            )
        if self.request.query_params.get("archived") is not None:
            return worksheets.filter(
                user__patrol__team__id=user.patrol.team.id,
                is_template=False,
                is_archived=True,
            )
        if user.function >= 5:
            return worksheets.filter(is_template=False, is_archived=False)
        if user.patrol and user.function >= 2:
            return worksheets.filter(
                Q(
                    user__patrol__team__id=user.patrol.team.id,
                    is_template=False,
                    is_archived=False,
                )
                | Q(supervisor__id=user.id, is_template=False, is_archived=False)
            )
        return worksheets.filter(user__id=user.id, is_template=False, is_archived=False)

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()
        remove_expired_deleted_worksheets()  # remove worksheets deleted more than 30 days ago

    def perform_create(self, serializer):
        if (
            serializer.validated_data.get("user") is None
            and serializer.validated_data.get("supervisor") is not None
        ):
            serializer.save(
                user=self.request.user,
                supervisor=serializer.validated_data.get("supervisor")["user"],
            )
            return
        if serializer.validated_data.get("user") is None:
            serializer.save(user=self.request.user)
            return
        if (
            serializer.validated_data.get("user")["user"] != self.request.user
            and self.request.user.function < 2
        ):
            raise PermissionDenied("You can't create worksheets for other user")
        if serializer.validated_data.get("supervisor") is None:
            serializer.save(
                user=serializer.validated_data.get("user"),
                supervisor=None,
            )
            return
        serializer.save(
            user=serializer.validated_data.get("user"),
            supervisor=serializer.validated_data.get("supervisor"),
        )


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == "WEB_MAINTENANCE_MODE" and old_value != new_value:
        set_maintenance_mode(new_value)
