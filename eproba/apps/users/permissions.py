from rest_framework import permissions


class IsAllowedToManageUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, user):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.scout.function >= 3
            and request.user.scout.function >= user.scout.function
            and request.user.scout.patrol
            and user.scout.patrol
            and request.user.scout.patrol.team == user.scout.patrol.team
        ) or (
            request.user.scout.function >= 3
            and request.user.scout.function >= user.scout.function
            and not user.scout.patrol
        )
