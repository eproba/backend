from django.contrib import admin

from .models import District, Patrol, Team, TeamRequest


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "district", "organization", "is_verified")
    list_filter = ("district", "is_verified", "organization")
    search_fields = ("name", "short_name")


@admin.register(Patrol)
class PatrolAdmin(admin.ModelAdmin):
    list_display = ("name", "team")
    list_filter = ("team",)
    search_fields = ("name", "team__name")


@admin.register(TeamRequest)
class TeamRequestAdmin(admin.ModelAdmin):
    list_display = ("team", "created_by", "status", "function_level", "created_at")
    list_filter = ("status", "function_level", "created_at")
    search_fields = ("team__name", "created_by__nickname")
    readonly_fields = ("created_by", "created_at")
    fieldsets = (
        (
            "Podstawowe informacje",
            {
                "fields": (
                    "team",
                    "created_by",
                    "function_level",
                    "status",
                    "accepted_by",
                ),
            },
        ),
        (
            "Dodatkowe informacje",
            {
                "fields": ("notes", "created_at"),
            },
        ),
    )
    actions = ["approve_requests", "reject_requests"]

    def approve_requests(self, request, queryset):
        queryset.update(status="approved")
        self.message_user(request, "Zgłoszenia zostały zaakceptowane.")

    approve_requests.short_description = "Zaakceptuj wybrane zgłoszenia"

    def reject_requests(self, request, queryset):
        queryset.update(status="rejected")
        self.message_user(request, "Zgłoszenia zostały odrzucone.")

    reject_requests.short_description = "Odrzuć wybrane zgłoszenia"
