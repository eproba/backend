from django.conf import settings
from django.core.mail import send_mail
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from ..models import TeamRequest
from ..permissions import IsAllowedToAccessTeamRequest
from ..serializers import TeamRequestSerializer


class TeamRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API do zarządzania zgłoszeniami drużyn.
    """

    serializer_class = TeamRequestSerializer
    permission_classes = [IsAllowedToAccessTeamRequest]

    def get_queryset(self):
        """
        Zwraca listę zgłoszeń drużyn z możliwością filtrowania po wielu statusach.
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
        Obsługuje standardowy PATCH na /api/team-requests/{id}/
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
                settings.DEFAULT_FROM_EMAIL,
                [team_request.created_by.email],
                fail_silently=True,
            )

        return Response(
            {"message": "Status zgłoszenia zaktualizowany."}, status=status.HTTP_200_OK
        )

    def get_email_content(self, team_request, send_note):
        """
        Generuje treść e-maila w zależności od statusu zgłoszenia.
        """
        team_name = team_request.team.name if team_request.team else "Twoja drużyna"
        note_text = (
            f"\n\nNotatka: {team_request.note}"
            if send_note and team_request.note
            else ""
        )

        patrol_links = "\n".join(
            [
                f"{patrol.name}: {patrol.get_registration_link()}"
                for patrol in team_request.team.patrols.all()
            ]
        )

        email_templates = {
            "approved": (
                "Twoje zgłoszenie zostało zaakceptowane!",
                f"""Drużyna {team_name} została zaakceptowana, możesz teraz korzystać ze wszystkich funkcji Epróby.

Możesz udostępnić link do częściowo wypełnionej rejestracji członkom swojej drużyny: {team_request.team.get_registration_link()}.
Lub dla konkretnego zastępu: 
{patrol_links}{note_text}""",
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
