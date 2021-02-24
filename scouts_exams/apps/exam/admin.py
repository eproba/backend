from django.contrib import admin

from .models import Task, Exam


class TaskInline(admin.TabularInline):
    model = Task
    exclude = ('key',)
    extra = 1


class ExamAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,{'fields': ['scout']}),
        (None,{'fields': ['name']}),
    ]
    inlines = [TaskInline]

admin.site.register(Exam, ExamAdmin)