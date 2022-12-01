from django.contrib import admin

from .models import Exam, Task


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1


class ExamAdmin(admin.ModelAdmin):
    list_filter = (
        "is_template",
        "is_archived",
        "scout__patrol__team",
    )

    super_list_filter = (
        "is_template",
        "is_archived",
        "deleted",
        "scout__patrol__team",
    )

    fieldsets = [
        (None, {"fields": ["scout", "supervisor"]}),
        (None, {"fields": ["name", "is_archived"]}),
        (None, {"fields": ["is_template"]}),
    ]

    super_fieldsets = [
        (None, {"fields": ["scout", "supervisor"]}),
        (None, {"fields": ["name", "is_archived", "deleted"]}),
        (None, {"fields": ["is_template"]}),
    ]

    inlines = [TaskInline]

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            self.fieldsets = self.super_fieldsets

        return super(ExamAdmin, self).get_form(request, obj, **kwargs)

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return self.super_list_filter
        return self.list_filter

    def get_queryset(self, request):
        qs = super(ExamAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(
                scout__patrol__team=request.user.scout.patrol.team
            ).exclude(deleted=True)
        return qs


admin.site.register(Exam, ExamAdmin)
