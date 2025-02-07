from apps.users.models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "email",
        "nickname",
        "is_superuser",
        "is_staff",
        "is_active",
        "first_name",
        "last_name",
        "patrol",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )
    normal_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "email_verified",
                    "password",
                    "nickname",
                    "first_name",
                    "last_name",
                    "gender",
                )
            },
        ),
        (
            "Scout",
            {
                "fields": (
                    "patrol",
                    (
                        "scout_rank",
                        "instructor_rank",
                        "function",
                    ),
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nickname",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
        (
            "Scout",
            {
                "fields": (
                    "patrol",
                    (
                        "scout_rank",
                        "instructor_rank",
                        "function",
                    ),
                )
            },
        ),
    )
    super_fieldsets = (
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "user_permissions",
                    "groups",
                )
            },
        ),
    )
    search_fields = ("email", "nickname", "first_name", "last_name")
    ordering = ("email",)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            self.fieldsets = self.normal_fieldsets + self.super_fieldsets
        else:
            self.fieldsets = self.normal_fieldsets

        return super(CustomUserAdmin, self).get_fieldsets(request, obj)


admin.site.register(User, CustomUserAdmin)
