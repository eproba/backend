from rest_framework import permissions


class IsAllowedToManageUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, user):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.function >= 3
            and request.user.function >= user.function
            and request.user.patrol
            and user.patrol
            and request.user.patrol.team == user.patrol.team
        ) or (
            request.user.function >= 3
            and request.user.function >= user.function
            and not user.patrol
        )
