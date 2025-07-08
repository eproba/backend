from apps.users.models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "email",
        "nickname",
        "full_name",
        "rank",
        "patrol",
        "is_superuser",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "scout_rank",
        "instructor_rank",
        "function",
    )
    search_fields = ("email", "nickname", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (
            "Podstawowe informacje",
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
            "Harcerz",
            {
                "fields": (
                    "patrol",
                    "scout_rank",
                    "instructor_rank",
                    "function",
                )
            },
        ),
        (
            "Uprawnienia",
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
        (
            "Dodatkowe informacje",
            {
                "fields": (
                    "created_at",
                    "email_notifications",
                    "is_deleted",
                    "deleted_at",
                ),
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
            "Harcerz",
            {
                "fields": (
                    "patrol",
                    "scout_rank",
                    "instructor_rank",
                    "function",
                )
            },
        ),
    )

    readonly_fields = ("created_at",)

    def full_name(self, obj):
        return obj.full_name or obj.email

    full_name.short_description = "Pełne imię"

    def rank(self, obj):
        return obj.rank()

    rank.short_description = "Stopień"

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return self.fieldsets
        return self.fieldsets[:2]


admin.site.register(User, CustomUserAdmin)
