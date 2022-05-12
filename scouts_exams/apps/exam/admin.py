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

    fieldsets = [
        (None, {"fields": ["scout", "supervisor"]}),
        (None, {"fields": ["name", "is_archived"]}),
        (None, {"fields": ["is_template"]}),
    ]
    inlines = [TaskInline]

    def get_queryset(self, request):
        qs = super(ExamAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(scout__patrol__team=request.user.scout.patrol.team)
        else:
            return qs


admin.site.register(Exam, ExamAdmin)
