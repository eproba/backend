from django.contrib import admin

from .models import Exam, Task


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1


class ExamAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["scout"]}),
        (None, {"fields": ["name"]}),
    ]
    inlines = [TaskInline]

    def get_queryset(self, request):
        qs = super(ExamAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(scout__team=request.user.scout.team)
        else:
            return qs


admin.site.register(Exam, ExamAdmin)
