from rest_framework import permissions


class IsAllowedToManageWorksheetOrReadOnlyForOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, worksheet):
        if request.method in permissions.SAFE_METHODS:
            return (
                (
                    request.user.function >= 2
                    and request.user.function >= worksheet.user.function
                    and request.user.patrol.team == worksheet.user.patrol.team
                )
                or worksheet.user == request.user
                or worksheet.supervisor == request.user
            )

        return (
            request.user.function >= 2
            and request.user.function >= worksheet.user.function
            and request.user.patrol.team == worksheet.user.patrol.team
        ) or worksheet.supervisor == request.user


class IsAllowedToManageTaskOrReadOnlyForOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        if request.method in permissions.SAFE_METHODS:
            return (
                (
                    request.user.function >= 2
                    and request.user.function >= task.worksheet.user.function
                    and request.user.patrol.team == task.worksheet.user.patrol.team
                )
                or task.worksheet.user == request.user
                or task.worksheet.supervisor == request.user
            )

        return (
            request.user.function >= 2
            and request.user.function >= task.worksheet.user.function
            and request.user.patrol.team == task.worksheet.user.patrol.team
        ) or task.worksheet.supervisor == request.user


class IsTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        return request.user == task.worksheet.user.user
