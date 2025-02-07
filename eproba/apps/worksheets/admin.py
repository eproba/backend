from django.contrib import admin

from .models import Task, Worksheet


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1


class WorksheetAdmin(admin.ModelAdmin):
    list_filter = (
        "is_template",
        "is_archived",
        "user__patrol__team",
    )

    super_list_filter = (
        "is_template",
        "is_archived",
        "deleted",
        "user__patrol__team",
    )

    fieldsets = [
        (None, {"fields": ["user", "supervisor"]}),
        (None, {"fields": ["name", "is_archived"]}),
        (None, {"fields": ["is_template"]}),
    ]

    super_fieldsets = [
        (None, {"fields": ["user", "supervisor"]}),
        (None, {"fields": ["name", "is_archived", "deleted"]}),
        (None, {"fields": ["is_template"]}),
    ]

    inlines = [TaskInline]

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            self.fieldsets = self.super_fieldsets

        return super(WorksheetAdmin, self).get_form(request, obj, **kwargs)

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return self.super_list_filter
        return self.list_filter

    def get_queryset(self, request):
        qs = super(WorksheetAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            if not request.user.patrol:
                return qs.filter(user__id=request.user.id)
            return qs.filter(user__patrol__team=request.user.patrol.team).exclude(
                deleted=True
            )
        return qs


admin.site.register(Worksheet, WorksheetAdmin)
