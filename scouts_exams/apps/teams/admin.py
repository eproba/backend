from apps.teams.models import Patrol, Team
from django.contrib import admin


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    fields = ("name", "short_name", "colors")
    list_display = ("name", "short_name", "colors")


@admin.register(Patrol)
class PatrolAdmin(admin.ModelAdmin):
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ("team",)
        return ()

    def get_list_display(self, request):
        if request.user.is_superuser:
            return "name", "team"
        return ("name",)

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return "name", "team"
        return ("name",)

    def get_queryset(self, request):
        qs = super(PatrolAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(team=request.user.scout.patrol.team)
        return qs
