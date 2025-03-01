from apps.users.models import User
from apps.users.tasks import clear_tokens
from apps.worksheets.models import Task, TemplateWorksheet, Worksheet
from apps.worksheets.tasks import remove_expired_deleted_worksheets
from apps.worksheets.utils import send_notification
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .permissions import (
    IsAllowedToManageTaskOrReadOnlyForOwner,
    IsAllowedToManageWorksheetOrReadOnlyForOwner,
    IsAllowedToReadOrManageTemplateWorksheet,
    IsTaskOwner,
)
from .serializers import (
    TaskSerializer,
    TemplateWorksheetSerializer,
    WorksheetSerializer,
)


class WorksheetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAllowedToManageWorksheetOrReadOnlyForOwner]
    serializer_class = WorksheetSerializer
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        last_sync = self.request.query_params.get("last_sync")
        qs = Worksheet.objects.all()
        if last_sync:
            from datetime import datetime

            qs = qs.filter(updated_at__gt=datetime.fromtimestamp(int(last_sync)))
        if self.request.query_params.get("user") is not None:
            return qs.filter(user=user, is_archived=False)
        if self.request.query_params.get("archived") is not None:
            return qs.filter(user__patrol__team=user.patrol.team, is_archived=True)
        # This is here for backward compatibility
        if self.request.query_params.get("templates") is not None:
            return TemplateWorksheet.objects.filter(
                Q(team=user.patrol.team)
                | Q(team=None, organization=user.patrol.team.organization)
            )
        # if user.function >= 5:
        #     return qs.filter(is_archived=False)
        # TODO: After updating function levels, change the above line to make more sense
        if user.patrol and user.function >= 2:
            return qs.filter(
                Q(user__patrol__team=user.patrol.team, is_archived=False)
                | Q(supervisor=user, is_archived=False)
            )
        return qs.filter(user=user, is_archived=False)

    def get_serializer_class(self):
        # This is here for backward compatibility
        if self.request.query_params.get("templates") is not None:
            return TemplateWorksheetSerializer
        return WorksheetSerializer

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()
        remove_expired_deleted_worksheets()  # remove worksheets deleted more than 30 days ago, it's here as a temporary solution

    def perform_create(self, serializer):
        if serializer.validated_data.get("user") is None:
            serializer.save(user=self.request.user)
        elif (
            serializer.validated_data.get("user") != self.request.user
            and self.request.user.function < 2
        ):
            raise PermissionDenied("You can't create worksheets for other user")
        else:
            serializer.save()


class TaskDetails(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAllowedToManageTaskOrReadOnlyForOwner]
    serializer_class = TaskSerializer
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.filter(
            worksheet__id=self.kwargs["worksheet_id"], id=self.kwargs["id"]
        )
        if user.function >= 5:
            return qs
        if user.patrol and user.function >= 2:
            return qs.filter(
                Q(
                    worksheet__user__patrol__team=user.patrol.team,
                    worksheet__is_archived=False,
                )
                | Q(worksheet__supervisor=user, worksheet__is_archived=False)
            )
        return qs.filter(worksheet__user=user)

    def perform_update(self, serializer):
        if serializer.validated_data.get("status") in [0, 2]:
            serializer.instance.approval_date = timezone.now()
            serializer.instance.approver = self.request.user
        serializer.save()
        serializer.instance.worksheet.save()
        clear_tokens()


class TemplateWorksheetViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsAllowedToReadOrManageTemplateWorksheet]
    serializer_class = TemplateWorksheetSerializer

    def get_queryset(self):
        if not self.request.user.patrol:
            return TemplateWorksheet.objects.none()
        return TemplateWorksheet.objects.filter(
            Q(team=self.request.user.patrol.team)
            | Q(team=None, organization=self.request.user.patrol.team.organization)
        )

    def perform_create(self, serializer):
        # Automatically set the team to the user's team if not provided
        if not serializer.validated_data.get("team"):
            serializer.save(team=self.request.user.patrol.team)
        else:
            serializer.save()

    def perform_update(self, serializer):
        # Optionally, you might check if the user is allowed to change the team
        serializer.save()


class TasksToBeChecked(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorksheetSerializer

    def get_queryset(self):
        return Worksheet.objects.filter(
            tasks__approver=self.request.user, tasks__status=1
        ).distinct()


class SubmitTask(APIView):
    permission_classes = [IsAuthenticated, IsTaskOwner]

    def post(self, request, *args, **kwargs):
        if request.data.get("approver") is None:
            return Response({"approver": "This field is required."}, status=422)
        task = get_object_or_404(
            Task, id=kwargs["id"], worksheet__id=kwargs["worksheet_id"]
        )
        if task.status == 2:
            return Response({"message": "Task already approved"})
        task.status = 1
        task.approver = User.objects.get(id=request.data["approver"])
        task.approval_date = timezone.now()
        task.save()
        send_notification(
            targets=task.approver,
            title="Nowe zadanie do sprawdzenia",
            body=f"Pojawił się nowy punkt do sprawdzenia dla {task.worksheet.user}",
            link=reverse("worksheets:check_tasks"),
        )
        return Response({"message": "Task submitted"})


class UnsubmitTask(APIView):
    permission_classes = [IsAuthenticated, IsTaskOwner]

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
