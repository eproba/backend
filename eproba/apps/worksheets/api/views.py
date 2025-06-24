import json

from apps.users.api.serializers import PublicUserSerializer
from apps.users.models import User
from apps.users.tasks import clear_tokens
from apps.worksheets.models import Task, TemplateWorksheet, Worksheet
from apps.worksheets.tasks import remove_expired_deleted_worksheets
from apps.worksheets.utils import send_notification
from django.db.models import Q
from django.http import QueryDict
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import ParseError, PermissionDenied
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


class MultipartNestedSupportMixin:
    """
    Mixin to handle multipart form data with nested JSON fields.
    Transforms JSON string fields to proper Python objects for serializers.
    """

    def transform_request_data(self, data):
        """Transform data structure to dictionary and parse JSON string fields."""
        # Transform data structure to dictionary
        force_dict_data = data
        if type(force_dict_data) is QueryDict:
            force_dict_data = force_dict_data.dict()

        # Transform JSON string to dictionary for each many field
        serializer = self.get_serializer()

        for key, value in serializer.get_fields().items():
            if isinstance(value, serializers.ListSerializer) or isinstance(
                value, serializers.ModelSerializer
            ):
                if key in force_dict_data and type(force_dict_data[key]) is str:
                    if force_dict_data[key] == "":
                        force_dict_data[key] = None
                    else:
                        try:
                            force_dict_data[key] = json.loads(force_dict_data[key])
                        except json.JSONDecodeError:
                            pass

        return force_dict_data

    def create(self, request, *args, **kwargs):
        """Override create to handle multipart nested data."""
        force_dict_data = self.transform_request_data(request.data)
        serializer = self.get_serializer(data=force_dict_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """Override update to handle multipart nested data."""
        force_dict_data = self.transform_request_data(request.data)
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=force_dict_data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


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
            return qs.filter(user=user)
        if self.request.query_params.get("archived") is not None:
            return qs.filter(user__patrol__team=user.patrol.team, is_archived=True)
        if self.request.query_params.get("review") is not None:
            return qs.filter(
                tasks__approver=self.request.user, tasks__status=1
            ).distinct()
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
        user_data = serializer.validated_data.get("user")
        user_id = user_data.get("id") if user_data else None

        if user_id:
            # Only function level 2+ can create worksheets for others
            if user_id != self.request.user.id and self.request.user.function < 2:
                raise PermissionDenied("You can't create worksheets for other user")

            from apps.users.models import User

            user = User.objects.get(id=user_id)
            serializer.save(user=user)
        else:
            # Default to current user if no user specified
            serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        user_data = serializer.validated_data.get("user")
        user_id = user_data.get("id") if user_data else None
        if user_id:
            if user_id != self.request.user.id and self.request.user.function < 2:
                raise PermissionDenied("You can't update worksheets for other user")

            from apps.users.models import User

            user = User.objects.get(id=user_id)
            serializer.validated_data["user"] = user
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


class TemplateWorksheetViewSet(MultipartNestedSupportMixin, ModelViewSet):
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
        if (
            not serializer.validated_data.get("team")
            and serializer.validated_data.get("organization") is None
        ):
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


class TaskActionView(APIView):
    def get_permissions(self):
        if self.kwargs.get("action") in ["submit", "unsubmit", "approvers"]:
            return [IsAuthenticated(), IsTaskOwner()]
        else:  # accept, reject, clear
            return [IsAuthenticated()]  # TODO: implement IsAllowedToManageTask

    def post(self, request, *args, **kwargs):
        action = kwargs.get("action")
        task = get_object_or_404(
            Task, id=kwargs["id"], worksheet__id=kwargs["worksheet_id"]
        )

        if action == "submit":
            return self.submit_task(request, task)
        elif action == "unsubmit":
            return self.unsubmit_task(task)
        elif action == "accept":
            return self.accept_task(request, task)
        elif action == "reject":
            return self.reject_task(request, task)
        elif action == "clear":
            return self.clear_status(request, task)
        raise ParseError("Invalid action")

    def get(self, request, *args, **kwargs):
        action = kwargs.get("action")
        task = get_object_or_404(
            Task, id=kwargs["id"], worksheet__id=kwargs["worksheet_id"]
        )

        if action == "approvers":
            return self.get_available_approvers(request, task)
        raise ParseError("Invalid action")

    def submit_task(self, request, task):
        if request.data.get("approver") is None:
            return Response({"detail": "Approver is required"}, status=422)
        if task.status == 1:
            raise ParseError("Task already submitted")
        if task.status == 2:
            raise ParseError("Task already approved")

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
        return Response(TaskSerializer(task).data)

    def unsubmit_task(self, task):
        if task.status != 1:
            raise ParseError("Task is not submitted")

        task.status = 0
        task.approver = None
        task.approval_date = None
        task.save()
        return Response(TaskSerializer(task).data)

    def accept_task(self, request, task):
        old_status = task.status
        task.status = 2
        task.approver = request.user
        task.approval_date = timezone.now()
        task.save()
        task.worksheet.save()  # Update worksheet timestamp

        if old_status != 2:
            send_notification(
                targets=task.approver,
                title="Zadanie zaakceptowane",
                body=f"Twoje zadanie zostało zaakceptowane przez {request.user}",
                link=reverse("worksheets:check_tasks"),
            )
        return Response(TaskSerializer(task).data)

    def reject_task(self, request, task):
        old_status = task.status
        task.status = 3
        task.approval_date = timezone.now()
        task.approver = request.user
        task.save()
        task.worksheet.save()  # Update worksheet timestamp

        if old_status not in [0, 3]:
            send_notification(
                targets=task.worksheet.user,
                title="Zadanie odrzucone",
                body=f"Twoje zadanie zostało odrzucone przez {request.user}",
                link=f"https://eproba.zhr.pl/worksheets/{task.worksheet.id}",
            )
        return Response(TaskSerializer(task).data)

    def clear_status(self, request, task):
        task.status = 0
        task.approval_date = None
        task.approver = None
        task.save()
        return Response(TaskSerializer(task).data)

    def get_available_approvers(self, request, task):
        if task.status in [1, 2]:
            raise PermissionDenied(
                "Task already submitted or approved, so you don't need that information"
            )

        available_approvers = []

        if task.worksheet.supervisor:
            available_approvers.append(task.worksheet.supervisor)

        if task.worksheet.user.patrol:
            available_approvers.extend(
                User.objects.filter(
                    patrol=task.worksheet.user.patrol,
                    function__gte=2,
                ).exclude(id=task.worksheet.user.id)
            )

            if task.worksheet.user.patrol.team:
                available_approvers.extend(
                    User.objects.filter(
                        patrol__team=task.worksheet.user.patrol.team,
                        function__gte=3,
                    ).exclude(id=task.worksheet.user.id)
                )

        available_approvers = list(set(available_approvers))
        return Response(PublicUserSerializer(available_approvers, many=True).data)
