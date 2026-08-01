import contextlib

# from: https://medium.datadriveninvestor.com/monitoring-user-actions-with-logentry-in-django-admin-8c9fbaa3f442
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import NotRegistered
from oauth2_provider.admin import AccessTokenAdmin as BaseAccessTokenAdmin
from oauth2_provider.admin import ApplicationAdmin as BaseApplicationAdmin
from oauth2_provider.admin import GrantAdmin as BaseGrantAdmin
from oauth2_provider.admin import IDTokenAdmin as BaseIDTokenAdmin
from oauth2_provider.admin import RefreshTokenAdmin as BaseRefreshTokenAdmin
from oauth2_provider.models import (
    get_access_token_model,
    get_application_model,
    get_grant_model,
    get_id_token_model,
    get_refresh_token_model,
)
from unfold.admin import ModelAdmin


@admin.register(LogEntry)
class LogEntryAdmin(ModelAdmin):
    # to have a date-based drilldown navigation in the admin page
    date_hierarchy = "action_time"

    # to filter the results by users, content types and action flags
    list_filter = ["content_type", "action_flag"]

    # when searching the user will be able to search in both object_repr and change_message
    search_fields = ["object_repr", "change_message"]

    list_display = [
        "action_time",
        "__str__",
        "user",
        "content_type",
        "action_flag",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Re-register django-oauth-toolkit models with Unfold-compatible admin classes.
Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()
RefreshToken = get_refresh_token_model()
IDToken = get_id_token_model()

for model in (Application, AccessToken, Grant, RefreshToken, IDToken):
    with contextlib.suppress(NotRegistered):
        admin.site.unregister(model)


@admin.register(Application)
class ApplicationAdmin(BaseApplicationAdmin, ModelAdmin):
    pass


@admin.register(AccessToken)
class AccessTokenAdmin(BaseAccessTokenAdmin, ModelAdmin):
    pass


@admin.register(Grant)
class GrantAdmin(BaseGrantAdmin, ModelAdmin):
    pass


@admin.register(RefreshToken)
class RefreshTokenAdmin(BaseRefreshTokenAdmin, ModelAdmin):
    pass


@admin.register(IDToken)
class IDTokenAdmin(BaseIDTokenAdmin, ModelAdmin):
    pass
