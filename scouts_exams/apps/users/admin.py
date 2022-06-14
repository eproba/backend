from apps.users.models import Scout, User
from apps.users.views import UserCreationForm
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    model = User
    list_display = (
        "email",
        "nickname",
        "is_superuser",
        "is_active",
        "first_name",
        "last_name",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )
    fieldsets = (
        (
            None,
            {"fields": ("email", "password", "nickname", "first_name", "last_name")},
        ),
    )
    super_fieldsets = (
        (
            None,
            {"fields": ("email", "password", "nickname", "first_name", "last_name")},
        ),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "is_superuser", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            self.fieldsets = self.super_fieldsets

        return super(CustomUserAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(CustomUserAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(scout__patrol__team=request.user.scout.patrol.team)
        return qs


admin.site.register(User, CustomUserAdmin)


@admin.register(Scout)
class EventAdmin(admin.ModelAdmin):
    fields = (
        "user",
        "patrol",
        (
            "rank",
            "function",
        ),
    )
    list_display = (
        "user",
        "user_nickname",
        "team_short_name",
        "patrol",
        "rank",
        "function",
    )
    list_filter = (
        "patrol__team",
        "patrol",
        "rank",
        "function",
    )

    def user_nickname(self, obj):
        return obj.user.nickname

    def get_queryset(self, request):
        qs = super(EventAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(patrol__team=request.user.scout.patrol.team)
        return qs

    def save_model(self, request, obj, form, change):
        if obj.user.is_superuser:
            obj.user.is_staff = True
            obj.user.save()
            obj.save()
        elif obj.function == 4:
            obj.user.is_staff = True
            obj.user.user_permissions.clear()
            for perm in [
                "delete_task",
                "change_user",
                "view_task",
                "change_scout",
                "view_exam",
                "add_patrol",
                "view_scout",
                "view_user",
                "add_task",
                "change_exam",
                "change_task",
                "delete_patrol",
                "change_team",
                "delete_exam",
                "add_exam",
                "view_patrol",
                "view_team",
                "change_patrol",
            ]:
                obj.user.user_permissions.add(Permission.objects.get(codename=perm))
            obj.user.save()
            obj.save()
        elif obj.function >= 5:
            obj.user.is_staff = True
            obj.user.user_permissions.clear()
            for perm in [
                "delete_task",
                "change_user",
                "view_task",
                "change_scout",
                "view_exam",
                "add_patrol",
                "view_scout",
                "view_user",
                "add_task",
                "change_exam",
                "change_task",
                "delete_patrol",
                "add_team",
                "change_team",
                "delete_exam",
                "add_exam",
                "view_patrol",
                "view_team",
                "change_patrol",
            ]:
                obj.user.user_permissions.add(Permission.objects.get(codename=perm))
            obj.user.save()
            obj.save()
        else:
            obj.user.is_staff = False
            obj.user.user_permissions.clear()
            obj.user.save()
            obj.save()
