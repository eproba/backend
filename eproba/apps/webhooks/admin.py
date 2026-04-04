from django.contrib import admin

from .models import Webhook


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "url", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__email", "url")
