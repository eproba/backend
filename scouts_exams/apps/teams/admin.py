from apps.teams.models import Patrol, Team
from django.contrib import admin


@admin.register(Team)
class EventAdmin(admin.ModelAdmin):
    fields = ("name", "short_name", "colors")
    list_display = ("name", "short_name", "colors")


@admin.register(Patrol)
class EventAdmin(admin.ModelAdmin):
    fields = ("name", "team")
    list_display = ("name", "team")
    list_filter = ("team",)

    def get_queryset(self, request):
        qs = super(EventAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(team=request.user.scout.patrol.team)
        else:
            return qs
