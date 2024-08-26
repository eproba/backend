from rest_framework import permissions


class IsAllowedToManageTeamOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, team):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            (
                request.user.function >= 4
                and request.user.patrol
                and request.user.patrol.team == team
                and team.is_verified
            )
            or (request.user.function >= 5 and team.is_verified)
            or (request.user.is_staff and request.user.has_perm("teams.change_team"))
            or request.user.is_superuser
        )


class IsAllowedToManagePatrolOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, patrol):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.function >= 3
            and request.user.patrol
            and request.user.patrol.team == patrol.team
        ) or request.user.function >= 5
