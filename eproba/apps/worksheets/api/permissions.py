from rest_framework import permissions


class IsAllowedToManageWorksheetOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, worksheet):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.function >= 2
            and (
                request.user.function >= worksheet.user.function
                or request.user.function >= 4
            )
            and request.user.patrol.team == worksheet.user.patrol.team
        ) or worksheet.supervisor == request.user


class IsAllowedToManageTaskOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        return IsAllowedToManageWorksheetOrReadOnly().has_object_permission(
            request, view, task.worksheet
        )


class IsTaskOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        return request.user == task.worksheet.user


class IsAllowedToReadOrManageTemplateWorksheet(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.patrol:
            return False

        if request.method in permissions.SAFE_METHODS:
            return request.user.function >= 2 or request.user.is_staff

        return request.user.function >= 3 or request.user.is_staff

    def has_object_permission(self, request, view, template_worksheet):
        is_team_template = template_worksheet.team == request.user.patrol.team

        is_org_template = (
            template_worksheet.team is None
            and template_worksheet.organization == request.user.patrol.team.organization
        )

        if request.method in permissions.SAFE_METHODS:
            return is_team_template or is_org_template

        if is_org_template:
            return request.user.is_staff and request.user.has_perm(
                "worksheets.change_templateworksheet"
            )

        if is_team_template:
            return request.user.function >= 3

        return False


class IsAllowedToAccessWorksheetNotes(permissions.BasePermission):
    def has_object_permission(self, request, view, worksheet):
        return (
            request.user.function >= 4 or worksheet.supervisor == request.user
        ) and request.user != worksheet.user


class IsAllowedToAccessTaskNotes(permissions.BasePermission):
    def has_object_permission(self, request, view, task):
        return IsAllowedToAccessWorksheetNotes().has_object_permission(
            request, view, task.worksheet
        )
