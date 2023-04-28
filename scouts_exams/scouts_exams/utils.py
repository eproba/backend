from datetime import datetime

from apps.exam.models import Exam, Task
from apps.exam.permissions import (
    IsAllowedToManageExamOrReadOnlyForOwner,
    IsAllowedToManageTaskOrReadOnlyForOwner,
    IsTaskOwner,
)
from apps.exam.serializers import ExamSerializer, TaskSerializer
from apps.teams.models import Patrol, Team
from apps.teams.permissions import (
    IsAllowedToManagePatrolOrReadOnly,
    IsAllowedToManageTeamOrReadOnly,
)
from apps.teams.serializers import PatrolSerializer, TeamSerializer
from apps.users.models import Scout, User
from apps.users.permissions import IsAllowedToManageUserOrReadOnly
from apps.users.serializers import PublicUserSerializer, UserSerializer
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


class UserViewSet(
    mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = PublicUserSerializer
    permission_classes = (IsAuthenticated, IsAllowedToManageUserOrReadOnly)

    def get_queryset(self):
        if self.request.query_params.get("team") is not None:
            return User.objects.filter(
                scout__patrol__team_id=self.request.query_params.get("team")
            )
        if self.request.user.scout.patrol is None:
            return User.objects.none()
        return User.objects.filter(
            Q(scout__patrol__team_id=self.request.user.scout.patrol.team.id)
            | Q(scout__patrol__isnull=True, is_active=False)
        )

    def perform_update(self, serializer):
        if serializer.validated_data.get("scout") is not None:
            scout = serializer.validated_data.get("scout")
            if scout.get("function") is not None:
                if scout.get("function") > self.request.user.scout.function:
                    raise PermissionDenied()
        if (
            serializer.instance.is_active is False
            and serializer.validated_data.get("is_active") is True
            and serializer.instance.scout.patrol is None
            and self.request.user.scout.patrol
        ):
            try:
                serializer.validated_data["scout"][
                    "patrol"
                ] = self.request.user.scout.patrol
            except KeyError:
                serializer.validated_data["scout"] = {
                    "patrol": self.request.user.scout.patrol
                }
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        instance = User.objects.get(pk=kwargs.get("pk"))
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
        if instance.scouts.count() > 0:
            if instance.scouts.filter(user__is_active=True).count() > 0:
                exception = APIException("Patrol has scouts")
                exception.status_code = 409
                raise exception
            if instance.team.patrol_set.count() > 1:
                for scout in instance.scouts.all():
                    scout.patrol = instance.team.patrol_set.exclude(
                        id=instance.id
                    ).first()
                    scout.save()
            else:
                for scout in instance.scouts.all():
                    scout.patrol = None
                    scout.function = 0
                    scout.save()
        instance.delete()

    def perform_create(self, serializer):
        if self.request.user.scout.function <= 2:
            raise PermissionDenied()
        if self.request.user.scout.function in [3, 4]:
            if serializer.validated_data.get("team") is not None:
                if (
                    serializer.validated_data.get("team").id
                    != self.request.user.scout.patrol.team.id
                ):
                    raise PermissionDenied()
                serializer.save()
            serializer.validated_data["team"] = self.request.user.scout.patrol.team
        serializer.save()


class TasksToBeChecked(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExamSerializer

    def get_queryset(self):
        return Exam.objects.filter(
            tasks__approver=self.request.user.scout, tasks__status=1
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
        if self.request.user.scout.function >= 5:
            return Task.objects.filter(exam__id=self.kwargs["exam_id"]).filter(
                id=self.kwargs["id"]
            )
        if self.request.user.scout.patrol and self.request.user.scout.function >= 2:
            return Task.objects.filter(
                Q(id=self.kwargs["id"])
                & Q(exam__id=self.kwargs["exam_id"])
                & Q(
                    exam__scout__patrol__team__id=self.request.user.scout.patrol.team.id,
                    exam__is_template=False,
                    exam__is_archived=False,
                )
                | Q(
                    exam__supervisor__user_id=self.request.user.id,
                    exam__is_template=False,
                    exam__is_archived=False,
                )
            )

        return Task.objects.filter(
            exam__id=self.kwargs["exam_id"], exam__scout__user__id=self.request.user.id
        ).filter(id=self.kwargs["id"])


class SubmitTask(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTaskOwner]

    def post(self, request, *args, **kwargs):
        if request.data.get("approver") is None:
            return Response({"approver": "This field is required."}, status=422)
        task = get_object_or_404(Task, id=kwargs["id"], exam__id=kwargs["exam_id"])
        if task.status == 2:
            return Response({"message": "Task already approved"})
        task.status = 1
        task.approver = Scout.objects.get(user_id=request.data["approver"])
        task.approval_date = timezone.now()
        task.save()
        FCMDevice.objects.filter(user=task.approver.user).send_message(
            Message(
                notification=Notification(
                    title="Nowe zadanie do sprawdzenia",
                    body=f"Pojawił się nowy punkt do sprawdzenia dla {task.exam.scout}.",
                ),
                webpush=WebpushConfig(
                    fcm_options=WebpushFCMOptions(
                        link="https://"
                        + request.get_host()
                        + reverse("exam:check_tasks")
                    ),
                ),
            )
        )
        return Response({"message": "Task submitted"})


class UnsubmitTask(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTaskOwner]

    def post(self, request, *args, **kwargs):
        task = get_object_or_404(Task, id=kwargs["id"], exam__id=kwargs["exam_id"])
        if task.status != 1:
            return Response({"message": "Task is not submitted"})
        task.status = 0
        task.approver = None
        task.approval_date = None
        task.save()
        return Response({"message": "Task unsubmitted"})


class ExamViewSet(ModelViewSet):
    permission_classes = [IsAllowedToManageExamOrReadOnlyForOwner, IsAuthenticated]
    serializer_class = ExamSerializer

    def get_queryset(self):
        last_sync = self.request.query_params.get("last_sync")
        if last_sync is not None:
            exams = Exam.objects.filter(
                updated_at__gt=datetime.fromtimestamp(int(last_sync))
            )
        else:
            exams = Exam.objects.all()
        user = self.request.user
        if self.request.query_params.get("user") is not None:
            return exams.filter(
                scout__user__id=user.id, is_template=False, is_archived=False
            )
        if self.request.query_params.get("templates") is not None:
            return exams.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                is_template=True,
                is_archived=False,
            )
        if self.request.query_params.get("archived") is not None:
            return exams.filter(
                scout__patrol__team__id=user.scout.patrol.team.id,
                is_template=False,
                is_archived=True,
            )
        if user.scout.function >= 5:
            return exams.filter(is_template=False, is_archived=False)
        if user.scout.patrol and user.scout.function >= 2:
            return exams.filter(
                Q(
                    scout__patrol__team__id=user.scout.patrol.team.id,
                    is_template=False,
                    is_archived=False,
                )
                | Q(supervisor__user_id=user.id, is_template=False, is_archived=False)
            )
        return exams.filter(
            scout__user__id=user.id, is_template=False, is_archived=False
        )

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()

    def perform_create(self, serializer):
        if (
            serializer.validated_data.get("scout") is None
            and serializer.validated_data.get("supervisor") is not None
        ):
            serializer.save(
                scout=self.request.user.scout,
                supervisor=serializer.validated_data.get("supervisor")["user"],
            )
            return
        if serializer.validated_data.get("scout") is None:
            serializer.save(scout=self.request.user.scout)
            return
        if (
            serializer.validated_data.get("scout")["user"] != self.request.user
            and self.request.user.scout.function < 2
        ):
            raise PermissionDenied("You can't create exam for other scout")
        if serializer.validated_data.get("supervisor") is None:
            serializer.save(
                scout=serializer.validated_data.get("scout")["user"].scout,
                supervisor=None,
            )
            return
        serializer.save(
            scout=serializer.validated_data.get("scout")["user"].scout,
            supervisor=serializer.validated_data.get("supervisor")["user"],
        )


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == "WEB_APP_MAINTENANCE":
        set_maintenance_mode(new_value)
