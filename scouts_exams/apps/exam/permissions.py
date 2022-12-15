from rest_framework import permissions


class IsAllowedToManageExamOrReadOnlyForOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, exam):
        if request.method in permissions.SAFE_METHODS:
            return (
                (
                    request.user.scout.function >= 2
                    and request.user.scout.function >= exam.scout.function
                )
                or exam.scout == request.user.scout
                or exam.supervisor == request.user.scout
            )

        return (
            request.user.scout.function >= 2
            and request.user.scout.function >= exam.scout.function
        )


class IsAllowedToManageTaskOrReadOnlyForOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        if request.method in permissions.SAFE_METHODS:
            return (
                (
                    request.user.scout.function >= 2
                    and request.user.scout.function >= task.exam.scout.function
                )
                or task.exam.scout == request.user.scout
                or task.exam.supervisor == request.user.scout
            )

        return (
            request.user.scout.function >= 2
            and request.user.scout.function >= task.exam.scout.function
        )


class IsTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        return request.user == task.exam.scout.user
