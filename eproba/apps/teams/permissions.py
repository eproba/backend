from rest_framework import permissions


class IsAllowedToManageTeamOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, team):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.scout.function >= 4
            and request.user.scout.patrol
            and request.user.scout.patrol.team == team
        ) or request.user.scout.function >= 5


class IsAllowedToManagePatrolOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, patrol):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.scout.function >= 3
            and request.user.scout.patrol
            and request.user.scout.patrol.team == patrol.team
        ) or request.user.scout.function >= 5
