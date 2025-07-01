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
        return request.user == task.worksheet.user


class IsAllowedToReadOrManageTemplateWorksheet(permissions.BasePermission):
    def has_object_permission(self, request, view, template_worksheet):
        if request.user.function < 2:
            return False

        is_team_template = template_worksheet.team == request.user.patrol.team

        is_org_template = (
            template_worksheet.team is None
            and template_worksheet.organization == request.user.patrol.team.organization
        )

        if request.method in permissions.SAFE_METHODS:
            return is_team_template or is_org_template

        if is_org_template and (
            not request.user.is_staff
            or not request.user.has_perm("worksheets.change_templateworksheet")
        ):
            return False

        return is_team_template or is_org_template
