from django.core.mail import send_mail
from django.db import transaction

from apps.teams.models import TeamRequest


TEAM_REQUEST_ADMIN_EMAIL = "eproba@zhr.pl"


def is_zhr_email(email: str) -> bool:
    """Return whether the address belongs to the primary ZHR email domain."""
    _, separator, domain = email.strip().lower().rpartition("@")
    return bool(separator) and domain == "zhr.pl"


def can_auto_approve_team_request(user) -> bool:
    return user.email_verified and is_zhr_email(user.email)


def get_team_request_outcome(team_request: TeamRequest) -> str:
    if team_request.status == "approved" and team_request.accepted_by_id is None:
        return "auto_approved"
    if (
        team_request.status in {"submitted", "pending_verification"}
        and is_zhr_email(team_request.created_by.email)
        and not team_request.created_by.email_verified
    ):
        return "can_auto_approve"
    return "awaiting_review"


@transaction.atomic
def set_team_request_status(
    team_request: TeamRequest,
    new_status: str,
    *,
    accepted_by=None,
    notes: str | None = None,
) -> TeamRequest:
    """Apply a team-request transition and keep related state consistent."""
    if new_status not in dict(TeamRequest.STATUS_CHOICES):
        raise ValueError("Invalid team request status")

    locked_request = (
        TeamRequest.objects.select_for_update()
        .select_related("team", "created_by")
        .get(pk=team_request.pk)
    )
    locked_request.status = new_status
    locked_request.accepted_by = accepted_by
    if notes is not None:
        locked_request.notes = notes
    locked_request.save(update_fields=["status", "accepted_by", "notes"])

    is_approved = new_status == "approved"
    locked_request.team.is_verified = is_approved
    locked_request.team.save(update_fields=["is_verified"])

    locked_request.created_by.function = (
        locked_request.function_level if is_approved else 0
    )
    locked_request.created_by.save(update_fields=["function"])

    return locked_request


def send_auto_approval_admin_email(team_request: TeamRequest) -> None:
    user = team_request.created_by
    send_mail(
        subject=f"Automatycznie zatwierdzono drużynę: {team_request.team.name}",
        message=(
            f"Adres {user.email} został zweryfikowany jako adres ZHR, dlatego "
            f"zgłoszenie drużyny {team_request.team.name} zostało automatycznie "
            "zatwierdzone. Nie wymaga ręcznej weryfikacji.\n\n"
            "Szczegóły: https://eproba.zhr.pl/team/requests/"
        ),
        from_email=None,
        recipient_list=[TEAM_REQUEST_ADMIN_EMAIL],
        fail_silently=True,
    )


def auto_approve_team_request_after_email_verification(user) -> TeamRequest | None:
    """Approve the user's current pending request after ZHR email verification."""
    if not can_auto_approve_team_request(user) or user.patrol_id is None:
        return None

    team_request = (
        TeamRequest.objects.select_related("team", "created_by")
        .filter(
            created_by=user,
            team_id=user.patrol.team_id,
            status__in=["submitted", "pending_verification"],
        )
        .order_by("-created_at")
        .first()
    )
    if team_request is None:
        return None

    team_request = set_team_request_status(team_request, "approved")
    send_auto_approval_admin_email(team_request)
    return team_request
