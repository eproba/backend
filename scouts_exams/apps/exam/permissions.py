from rest_framework import permissions


class IsAllowedToManageExamOrReadOnlyForOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return (
                request.user.scout.function >= 2
                and request.user.scout.function >= obj.scout.function
            ) or obj.scout == request.user.scout

        return (
            request.user.scout.function >= 2
            and request.user.scout.function >= obj.scout.function
        )
