import threading
from datetime import timedelta

from apps.teams.api.permissions import (
    IsAllowedToAccessTeamRequest,
    IsAllowedToAccessTeamStats,
)
from apps.teams.api.serializers import TeamRequestSerializer
from apps.teams.models import District, Patrol, Team, TeamRequest
from apps.users.models import (
    User,
    instructor_rank_female,
    instructor_rank_male,
    scout_rank_female,
    scout_rank_male,
)
from apps.worksheets.models import Task, Worksheet
from django.core.mail import EmailMessage, send_mail
from django.db.models import Count, Max, OuterRef, Q, Subquery
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import (
    IsAllowedToManagePatrolOrReadOnly,
    IsAllowedToManageTeamOrReadOnly,
)
from .serializers import (
    DistrictSerializer,
    PatrolSerializer,
    TeamMetaSerializer,
    TeamSerializer,
)


def send_team_request_email(team_request_obj):
    """
    Send email notification when a new team request is created
    """
    email = EmailMessage(
        subject=f"Zgłoszenie o dodanie drużyny: {team_request_obj.team.name}",
        body="Pojawiło się nowe zgłoszenie o dodanie drużyny. https://eproba.zhr.pl/team/requests/",
        from_email=None,
        to=["eproba@zhr.pl"],
        headers={"Reply-To": team_request_obj.created_by.email},
    )
    email.send()


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


class TeamViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, IsAllowedToManageTeamOrReadOnly]

    def get_queryset(self):
        district = self.request.GET.get("district")
        is_verified = self.request.GET.get("is_verified")
        organization = self.request.GET.get("organization")
        qs = Team.objects.all()
        if self.request.GET.get("user") is not None:
            qs = qs.filter(patrols__users=self.request.user)
        if district:
            qs = qs.filter(district=district)
        if is_verified is not None:
            qs = qs.filter(is_verified=is_verified.lower() == "true")
        if organization:
            qs = qs.filter(organization=int(organization))
        return qs

    def get_serializer_class(self):
        if self.action == "list" and not self.request.GET.get("user") is not None:
            return TeamMetaSerializer
        return TeamSerializer


class PatrolViewSet(viewsets.ModelViewSet):
    queryset = Patrol.objects.all()
    serializer_class = PatrolSerializer
    permission_classes = [IsAuthenticated, IsAllowedToManagePatrolOrReadOnly]

    def perform_destroy(self, instance):
        # Prevent deletion if patrol has active users
        if instance.users.filter(is_active=True).exists():
            exc = APIException("Patrol has active users.")
            exc.status_code = 409
            raise exc
        instance.users.filter(is_active=False).update(
            patrol=instance.team.patrols.first()
        )
        instance.delete()


class TeamRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API do zarządzania zgłoszeniami drużyn.
    """

    serializer_class = TeamRequestSerializer
    permission_classes = [
        IsAuthenticated,
        IsAllowedToAccessTeamRequest,
    ]

    def perform_create(self, serializer):
        """
        Create a new team request and send email notification
        """
        team_request = serializer.save()

        # Send email notification in background
        send_email_thread = threading.Thread(
            target=send_team_request_email, args=(team_request,), daemon=True
        )
        send_email_thread.start()

    def get_queryset(self):
        """
        Retrieve all team requests, optionally filtered by status.
        """
        queryset = TeamRequest.objects.all().order_by("-created_at")
        status_filter = self.request.query_params.get("status")

        if status_filter:
            status_list = [s.strip() for s in status_filter.split(",") if s.strip()]
            valid_statuses = {s for s, _ in TeamRequest.STATUS_CHOICES}
            filtered_statuses = [s for s in status_list if s in valid_statuses]

            if filtered_statuses:
                queryset = queryset.filter(status__in=filtered_statuses)

        return queryset

    def update(self, request, *args, **kwargs):
        """
        Handle updating the status of a team request.
        Allows changing the status, adding a note, and sending an email notification.
        """
        team_request = self.get_object()

        note = request.data.get("note", "").strip()
        send_email = request.data.get("send_email", True)
        send_note = request.data.get("send_note", False)
        new_status = request.data.get("status")

        if new_status not in dict(TeamRequest.STATUS_CHOICES):
            return Response(
                {"error": "Niepoprawny status."}, status=status.HTTP_400_BAD_REQUEST
            )

        team_request.status = new_status
        team_request.note = note
        team_request.save()

        team_request.team.is_verified = new_status == "approved"
        team_request.team.save()

        team_request.created_by.function = team_request.function_level
        team_request.created_by.save()

        team_request.accepted_by = request.user
        team_request.save()

        if send_email:
            subject, message = self.get_email_content(team_request, send_note)
            send_mail(
                subject,
                message,
                None,
                [team_request.created_by.email],
                fail_silently=True,
            )

        return Response(
            {"message": "Status zgłoszenia zaktualizowany."}, status=status.HTTP_200_OK
        )

    def get_email_content(self, team_request, send_note):
        """
        Generates the email content based on the team request status.
        """
        team_name = team_request.team.name if team_request.team else "Twoja drużyna"
        note_text = (
            f"\n\nNotatka: {team_request.note}"
            if send_note and team_request.note
            else ""
        )

        email_templates = {
            "approved": (
                "Twoje zgłoszenie zostało zaakceptowane!",
                f"""Drużyna {team_name} została zaakceptowana, możesz teraz korzystać ze wszystkich funkcji Epróby.

Link: https://eproba.zhr.pl{note_text}""",
            ),
            "rejected": (
                "Twoje zgłoszenie zostało odrzucone",
                f"Zgłoszenie drużyny {team_name} zostało odrzucone.{note_text}",
            ),
            "pending_verification": (
                "Twoje zgłoszenie wymaga dodatkowej weryfikacji",
                f"Drużyna {team_name} wymaga dodatkowej weryfikacji.{note_text}",
            ),
            "submitted": (
                "Twoje zgłoszenie zostało zaktualizowane",
                f"Zgłoszenie dla drużyny {team_name} zostało ponownie przesłane, wkrótce otrzymasz odpowiedź.{note_text}",
            ),
        }

        return email_templates.get(
            team_request.status,
            (
                "Aktualizacja zgłoszenia",
                f"Twoje zgłoszenie zostało zaktualizowane.{note_text}",
            ),
        )


class TeamStatisticsAPIView(APIView):
    """
    API endpoint providing comprehensive team statistics for team leaders.

    Provides metrics including:
    - Team overview (member counts, activity)
    - Rank distribution
    - Worksheet/badge progress
    - Activity trends
    - Patrol comparisons
    """

    permission_classes = [IsAuthenticated, IsAllowedToAccessTeamStats]

    def get(self, request):
        user = request.user
        team = user.patrol.team
        stats = self._calculate_team_statistics(team, user)

        return Response(stats, status=status.HTTP_200_OK)

    def _calculate_team_statistics(self, team, current_user):
        """Calculate comprehensive team statistics"""
        organization = team.organization

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        # Basic team info
        team_members = User.objects.filter(patrol__team=team, is_active=True)
        total_members = team_members.count()

        # TEAM OVERVIEW STATS
        overview_stats = {
            "total_members": total_members,
            "verified_emails": team_members.filter(email_verified=True).count(),
            "active_last_30_days": team_members.filter(
                worksheets__updated_at__gte=thirty_days_ago, worksheets__deleted=False
            )
            .distinct()
            .count(),
            "patrols_count": team.patrols.count(),
        }

        # RANK DISTRIBUTION
        rank_distribution = {
            "scout_ranks": self._get_scout_rank_distribution(
                team_members, organization
            ),
            "instructor_ranks": self._get_instructor_rank_distribution(
                team_members, organization
            ),
            "functions": self._get_function_distribution(team_members, organization),
        }

        # WORKSHEET/BADGE PROGRESS
        worksheets = Worksheet.objects.filter(user__patrol__team=team, deleted=False)

        archived_worksheets = worksheets.filter(is_archived=True).count()

        active_fully_completed = 0
        for worksheet in worksheets.filter(is_archived=False):
            total_tasks = worksheet.tasks.count()
            if total_tasks > 0:
                completed_tasks = worksheet.tasks.filter(status=2).count()
                if total_tasks == completed_tasks:
                    active_fully_completed += 1

        worksheet_stats = {
            "total_worksheets": worksheets.count(),
            "active_worksheets": worksheets.filter(is_archived=False).count(),
            "completed_worksheets": archived_worksheets + active_fully_completed,
            "average_completion_rate": self._calculate_average_completion_rate(
                worksheets
            ),
            "pending_approvals": Task.objects.filter(
                worksheet__user__patrol__team=team, status=1, worksheet__deleted=False
            ).count(),
        }

        # ACTIVITY TRENDS
        activity_trends = {
            "worksheets_created_last_7_days": worksheets.filter(
                created_at__gte=seven_days_ago
            ).count(),
            "worksheets_created_last_30_days": worksheets.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            "tasks_completed_last_7_days": Task.objects.filter(
                worksheet__user__patrol__team=team,
                worksheet__deleted=False,
                status=2,
                approval_date__gte=seven_days_ago,
            ).count(),
            "tasks_completed_last_30_days": Task.objects.filter(
                worksheet__user__patrol__team=team,
                worksheet__deleted=False,
                status=2,
                approval_date__gte=thirty_days_ago,
            ).count(),
        }

        # PATROL COMPARISONS
        patrol_stats = self._get_patrol_statistics(team, organization)

        # TOP PERFORMERS
        top_performers = self._get_top_performers(team)

        # INACTIVE MEMBERS (need attention)
        inactive_members = self._get_inactive_members(team)

        return {
            "team_info": {
                "name": team.name,
                "short_name": team.short_name,
                "district": team.district.name,
                "organization": team.get_organization_display(),
                "is_verified": team.is_verified,
            },
            "overview": overview_stats,
            "rank_distribution": rank_distribution,
            "worksheet_progress": worksheet_stats,
            "activity_trends": activity_trends,
            "patrol_comparison": patrol_stats,
            "top_performers": top_performers,
            "members_needing_attention": inactive_members,
            "generated_at": now.isoformat(),
        }

    def _get_scout_rank_distribution(self, team_members, organization):
        """Get distribution of scout ranks with organization-specific labels"""
        ranks = team_members.values("scout_rank").annotate(count=Count("id"))

        if organization == 0:
            scout_rank_labels = scout_rank_male
        else:
            scout_rank_labels = scout_rank_female

        return [
            {
                "rank": scout_rank_labels.get(item["scout_rank"], "brak stopnia"),
                "rank_value": item["scout_rank"],
                "count": item["count"],
            }
            for item in ranks
        ]

    def _get_instructor_rank_distribution(self, team_members, organization):
        """Get distribution of instructor ranks with organization-specific labels"""
        ranks = team_members.values("instructor_rank").annotate(count=Count("id"))

        if organization == 0:
            instructor_rank_labels = instructor_rank_male
        else:
            instructor_rank_labels = instructor_rank_female

        return [
            {
                "rank": instructor_rank_labels.get(
                    item["instructor_rank"], "brak stopnia"
                ),
                "rank_value": item["instructor_rank"],
                "count": item["count"],
            }
            for item in ranks
        ]

    def _get_function_distribution(self, team_members, organization):
        """Get distribution of scout functions with organization-specific rank breakdown for bar graphs"""

        if organization == 0:
            function_choices = {
                0: "Druh",
                1: "Podzastępowy",
                2: "Zastępowy",
                3: "Przyboczny",
                4: "Drużynowy",
                5: "Wyższa funkcja",
            }
            scout_rank_labels = scout_rank_male
        else:
            function_choices = {
                0: "Druhna",
                1: "Podzastępowa",
                2: "Zastępowa",
                3: "Przyboczna",
                4: "Drużynowa",
                5: "Wyższa funkcja",
            }
            scout_rank_labels = scout_rank_female

        functions = team_members.values("function").annotate(count=Count("id"))

        function_data = []
        for function_item in functions:
            function_value = function_item["function"]
            function_name = function_choices.get(function_value, "Unknown")

            function_members = team_members.filter(function=function_value)
            rank_distribution = function_members.values("scout_rank").annotate(
                count=Count("id")
            )

            rank_breakdown = []
            total_count = 0
            for rank_item in rank_distribution:
                rank_value = rank_item["scout_rank"]
                rank_count = rank_item["count"]
                total_count += rank_count

                rank_breakdown.append(
                    {
                        "rank": scout_rank_labels.get(rank_value, "brak stopnia"),
                        "rank_value": rank_value,
                        "count": rank_count,
                    }
                )

            rank_breakdown.sort(key=lambda x: x["rank_value"])

            function_data.append(
                {
                    "function": function_name,
                    "function_value": function_value,
                    "total_count": total_count,
                    "rank_breakdown": rank_breakdown,
                }
            )

        function_data.sort(key=lambda x: x["function_value"])

        return function_data

    def _calculate_average_completion_rate(self, worksheets):
        """Calculate average completion rate across all worksheets"""
        active_worksheets = worksheets.filter(is_archived=False)
        if not active_worksheets.exists():
            return 0

        total_rate = 0
        count = 0

        for worksheet in active_worksheets:
            total_tasks = worksheet.tasks.count()
            if total_tasks > 0:
                completed_tasks = worksheet.tasks.filter(status=2).count()
                total_rate += (completed_tasks / total_tasks) * 100
                count += 1

        return round(total_rate / count, 1) if count > 0 else 0

    def _get_patrol_statistics(self, team, organization):
        """Get statistics for each patrol"""
        patrols = team.patrols.annotate(
            member_count=Count("users", filter=Q(users__is_active=True), distinct=True)
        )

        patrol_data = []
        for patrol in patrols:
            member_count = getattr(patrol, "member_count", 0)

            worksheet_count = Worksheet.objects.filter(
                user__patrol=patrol, deleted=False
            ).count()

            completed_worksheets = Worksheet.objects.filter(
                user__patrol=patrol, deleted=False, is_archived=True
            ).count()

            active_completed = 0
            for worksheet in Worksheet.objects.filter(
                user__patrol=patrol, deleted=False, is_archived=False
            ):
                total_tasks = worksheet.tasks.count()
                if total_tasks > 0:
                    completed_tasks = worksheet.tasks.filter(status=2).count()
                    if total_tasks == completed_tasks:
                        active_completed += 1

            completed_worksheets += active_completed

            average_completion_rate = 0
            active_worksheets = Worksheet.objects.filter(
                user__patrol=patrol, deleted=False, is_archived=False
            )

            if active_worksheets.exists():
                total_completion_rate = 0
                count = 0
                for worksheet in active_worksheets:
                    total_tasks = worksheet.tasks.count()
                    if total_tasks > 0:
                        completed_tasks = worksheet.tasks.filter(status=2).count()
                        task_completion_rate = (completed_tasks / total_tasks) * 100
                        total_completion_rate += task_completion_rate
                        count += 1
                average_completion_rate = (
                    round(total_completion_rate / count, 1) if count > 0 else 0
                )

            patrol_data.append(
                {
                    "id": str(patrol.id),
                    "name": patrol.name,
                    "member_count": member_count,
                    "worksheet_count": worksheet_count,
                    "average_completion_rate": average_completion_rate,
                    "average_rank": self._get_patrol_average_rank(patrol, organization),
                }
            )

        return patrol_data

    def _get_patrol_average_rank(self, patrol, organization):
        """Calculate average scout rank for patrol"""
        members = patrol.users.filter(is_active=True)
        if not members.exists():
            return "brak stopnia"

        if organization == 0:
            scout_rank_labels = scout_rank_male
        else:
            scout_rank_labels = scout_rank_female

        total_rank = sum(member.scout_rank for member in members)
        return scout_rank_labels.get(
            round(total_rank / members.count(), 1), "brak stopnia"
        )

    def _get_top_performers(self, team):
        """Get top performing scouts based on tasks completed in last 90 days"""
        time_from = timezone.now() - timedelta(days=90)

        members = (
            User.objects.filter(patrol__team=team, is_active=True)
            .annotate(
                completed_tasks=Count(
                    "worksheets__tasks",
                    filter=Q(
                        worksheets__tasks__status=2,
                        worksheets__tasks__approval_date__gte=time_from,
                        worksheets__deleted=False,
                    ),
                    distinct=True,
                ),
                total_worksheets=Count(
                    "worksheets", filter=Q(worksheets__deleted=False), distinct=True
                ),
            )
            .order_by("-completed_tasks")[:10]
        )

        top_performers = []
        for member in members:
            completed_tasks = getattr(member, "completed_tasks", 0)
            if completed_tasks > 0:
                top_performers.append(
                    {
                        "id": str(member.id),
                        "name": member.full_name_nickname(),
                        "patrol": member.patrol.name if member.patrol else None,
                        "rank": member.rank() or "brak stopnia",
                        "completed_tasks": completed_tasks,
                        "total_worksheets": getattr(member, "total_worksheets", 0),
                    }
                )

        return top_performers

    def _get_inactive_members(self, team):
        """Get members who need attention (inactive in last 90 days)"""
        time_from = timezone.now() - timedelta(days=90)

        # Subquery to check if user has recent completed tasks
        recent_completed_tasks = User.objects.filter(
            id=OuterRef("id"),
            worksheets__tasks__approval_date__gte=time_from,
            worksheets__tasks__status=2,
            worksheets__deleted=False,
        ).values("id")[:1]

        inactive = (
            User.objects.filter(
                patrol__team=team, is_active=True, created_at__lt=time_from
            )
            .exclude(id__in=Subquery(recent_completed_tasks))
            .annotate(
                worksheet_count=Count(
                    "worksheets", filter=Q(worksheets__deleted=False), distinct=True
                ),
                last_task_completion=Max(
                    "worksheets__tasks__approval_date",
                    filter=Q(worksheets__tasks__status=2, worksheets__deleted=False),
                ),
            )
            .order_by("last_task_completion", "created_at")
        )

        inactive_members = []
        for member in inactive:
            worksheet_count = getattr(member, "worksheet_count", 0)
            last_completion = getattr(member, "last_task_completion", None)

            if last_completion:
                days_since_last_activity = (timezone.now() - last_completion).days
            else:
                days_since_last_activity = (timezone.now() - member.created_at).days

            inactive_members.append(
                {
                    "id": str(member.id),
                    "name": member.full_name_nickname(),
                    "patrol": member.patrol.name if member.patrol else None,
                    "rank": member.rank() or "brak stopnia",
                    "total_worksheets": worksheet_count,
                    "days_inactive": days_since_last_activity,
                    "last_activity": (
                        last_completion.isoformat() if last_completion else None
                    ),
                }
            )

        return inactive_members
