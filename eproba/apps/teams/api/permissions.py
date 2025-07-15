from apps.users.models import User
from rest_framework import permissions


class IsAllowedToManageTeamOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, team):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.patrol is not None
            and request.user.patrol.team == team
            and (
                request.user.function >= 4
                or (
                    request.user.function >= 3
                    and not User.objects.filter(
                        patrol__team=team, is_active=True, function__gt=3
                    ).exists()
                )
            )
        )


class IsAllowedToManagePatrolOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, patrol):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.function >= 3
            and request.user.patrol is not None
            and request.user.patrol.team == patrol.team
        )


class IsAllowedToAccessTeamRequest(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return True

        return (
            request.user.is_staff
            and request.user.has_perm("teams.change_team")
            and request.user.has_perm("teams.change_teamrequest")
        ) or request.user.is_superuser


class IsAllowedToAccessTeamStats(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.function >= 3
            and request.user.patrol is not None
        )
