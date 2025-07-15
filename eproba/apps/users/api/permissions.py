from apps.users.models import User
from rest_framework import permissions


class IsAllowedToManageUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, user):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.patrol is not None
            and user.patrol is not None
            and request.user.patrol.team == user.patrol.team
            and (
                request.user.function >= 4
                or (
                    request.user.function >= 3
                    and (
                        user.function < 4
                        or not User.objects.filter(
                            patrol__team=request.user.patrol.team,
                            is_active=True,
                            function__gt=3,
                        ).exists()
                    )
                )
            )
        )
