import json
from datetime import datetime

from apps.users.api.serializers import PublicUserSerializer
from apps.users.models import User
from apps.users.tasks import clear_tokens
from apps.users.utils import send_notification
from apps.worksheets.models import Task, TemplateWorksheet, Worksheet
from apps.worksheets.tasks import remove_expired_deleted_worksheets
from django.db.models import Q
from django.http import QueryDict
from django.urls import reverse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ParseError, PermissionDenied
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .permissions import (
    IsAllowedToAccessTaskNotes,
    IsAllowedToAccessWorksheetNotes,
    IsAllowedToManageTaskOrReadOnly,
    IsAllowedToManageWorksheetOrReadOnly,
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
    permission_classes = [IsAuthenticated, IsAllowedToManageWorksheetOrReadOnly]
    serializer_class = WorksheetSerializer
    lookup_field = "id"

    def get_queryset(self):
        qs = Worksheet.objects.all()
        if self.action == "retrieve":
            return qs.filter(deleted=False)

        user = self.request.user
        last_sync = self.request.query_params.get("last_sync")
        if last_sync:
            qs = qs.filter(updated_at__gt=datetime.fromtimestamp(int(last_sync)))
        if self.request.query_params.get("user") is not None:
            return qs.filter(user=user)
        if self.request.query_params.get("archived") is not None:
            if not user.patrol:
                return qs.filter(user=user, is_archived=True)
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

            user = User.objects.get(id=user_id)
            serializer.save(user=user)
        else:
            # Default to current user if no user specified
            serializer.save(user=self.request.user)

        if serializer.instance.user != self.request.user:
            send_notification(
                targets=serializer.instance.user,
                title=f'Próba "{serializer.instance.name}" została utworzona dla Ciebie',
                body=f'Próba "{serializer.instance.name}" została utworzona przez {self.request.user.full_name_nickname()}',
                link=f"worksheets#{serializer.instance.id}",
            )

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

    @action(
        detail=True,
        methods=["post", "put", "delete"],
        url_name="note",
        url_path="note",
        permission_classes=[IsAuthenticated, IsAllowedToAccessWorksheetNotes],
    )
    def manage_note(self, request, id=None):
        """Manage notes on worksheet"""
        worksheet = self.get_object()

        if request.method in ["POST", "PUT"]:
            note_content = request.data.get("notes", "")
            if not isinstance(note_content, str):
                return Response(
                    {"detail": "Note must be a string"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            worksheet.notes = note_content
            worksheet.save()

            return Response(self.get_serializer(worksheet).data)

        elif request.method == "DELETE":
            worksheet.notes = ""
            worksheet.save()

            return Response(self.get_serializer(worksheet).data)

        raise MethodNotAllowed(
            method=request.method,
        )


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
        if (
            serializer.validated_data.get("scope") == "organization"
            and not self.request.user.is_staff
        ):
            raise PermissionDenied("You can't create organization templates")
        serializer.save()

    def perform_update(self, serializer):
        if (
            serializer.validated_data.get("scope") == "organization"
            and not self.request.user.is_staff
        ):
            raise PermissionDenied(
                "You can't update this template to organization scope"
            )
        if (
            serializer.validated_data.get("scope") == "team"
            and not self.request.user.function >= 3
        ):
            raise PermissionDenied("You can't update this template to team scope")
        serializer.save()


@extend_schema(deprecated=True)
class TasksToBeChecked(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorksheetSerializer

    def get_queryset(self):
        return Worksheet.objects.filter(
            tasks__approver=self.request.user, tasks__status=1
        ).distinct()


@extend_schema(deprecated=True)
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


@extend_schema(deprecated=True)
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


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for task CRUD operations and actions.
    """

    serializer_class = TaskSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Task.objects.filter(worksheet__id=self.kwargs.get("worksheet_id"))

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ["submit", "unsubmit", "get_approvers"]:
            return [IsAuthenticated(), IsTaskOwner()]
        elif self.action in ["accept", "reject", "clear_status"]:
            return [IsAuthenticated(), IsAllowedToManageTaskOrReadOnly()]
        elif self.action == "manage_note":
            return [IsAuthenticated(), IsAllowedToAccessTaskNotes()]
        elif self.action in ["retrieve", "partial_update", "update"]:
            return [IsAuthenticated(), IsAllowedToManageTaskOrReadOnly()]
        return super().get_permissions()

    def perform_update(self, serializer):
        """Override update behavior from old TaskDetails"""
        if serializer.validated_data.get("status") in [0, 2]:
            serializer.instance.approval_date = timezone.now()
            serializer.instance.approver = self.request.user
        serializer.save()
        serializer.instance.worksheet.save()
        clear_tokens()

    @action(detail=True, methods=["post"])
    def submit(self, request, *args, **kwargs):
        """Submit task for approval"""
        task = self.get_object()

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
            title=f"Nowe zadanie do sprawdzenia: {task.task}",
            body=f"Pojawił się nowy punkt do sprawdzenia dla {task.worksheet.user}",
            link=f"worksheets/review#{task.worksheet.id}",
        )
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"])
    def unsubmit(self, request, *args, **kwargs):
        """Unsubmit task"""
        task = self.get_object()

        if task.status != 1:
            raise ParseError("Task is not submitted")

        task.status = 0
        task.approver = None
        task.approval_date = None
        task.save()
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"])
    def accept(self, request, *args, **kwargs):
        """Accept task"""
        task = self.get_object()
        old_status = task.status

        task.status = 2
        task.approver = request.user
        task.approval_date = timezone.now()
        task.save()
        task.worksheet.save()  # Update worksheet timestamp

        if old_status != 2 and request.user != task.worksheet.user:
            send_notification(
                targets=task.worksheet.user,
                title=f"Zadanie zaakceptowane: {task.task}",
                body=f"Twoje zadanie zostało zaakceptowane przez {request.user}",
                link=f"worksheets#{task.worksheet.id}",
            )
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, *args, **kwargs):
        """Reject task"""
        task = self.get_object()
        old_status = task.status

        task.status = 3
        task.approval_date = timezone.now()
        task.approver = request.user
        task.save()
        task.worksheet.save()  # Update worksheet timestamp

        if old_status not in [0, 3] and request.user != task.worksheet.user:
            send_notification(
                targets=task.worksheet.user,
                title=f"Zadanie odrzucone: {task.task}",
                body=f"Twoje zadanie zostało odrzucone przez {request.user}",
                link=f"worksheets#{task.worksheet.id}",
            )
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"])
    def clear_status(self, request, *args, **kwargs):
        """Clear task status"""
        task = self.get_object()

        task.status = 0
        task.approval_date = None
        task.approver = None
        task.save()
        return Response(self.get_serializer(task).data)

    @action(
        detail=True,
        methods=["post", "put", "delete"],
        url_name="note",
    )
    def manage_note(self, request, *args, **kwargs):
        task = self.get_object()

        if request.method in ["POST", "PUT"]:
            note_content = request.data.get("notes", "")
            if not isinstance(note_content, str):
                return Response(
                    {"detail": "Note must be a string"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            task.notes = note_content
            task.save()

            return Response(self.get_serializer(task).data)

        elif request.method == "DELETE":
            task.notes = ""
            task.save()

            return Response(self.get_serializer(task).data)

        raise MethodNotAllowed(
            method=request.method,
        )

    @action(detail=True, methods=["get"], url_name="approvers")
    def get_approvers(self, request, *args, **kwargs):
        """Get available approvers for task"""
        task = self.get_object()

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
                    patrol__team=task.worksheet.user.patrol.team,
                    function__gte=3,
                ).exclude(id=task.worksheet.user.id)
            )

            if task.category == "general":
                available_approvers.extend(
                    User.objects.filter(
                        patrol__team=task.worksheet.user.patrol.team,
                        function__gte=2,
                    )
                )

        available_approvers = list(set(available_approvers))
        return Response(PublicUserSerializer(available_approvers, many=True).data)


@extend_schema(deprecated=True)
class LegacyTaskViewSet(TaskViewSet):
    pass
