from apps.users.models import Scout, User
from apps.users.views import UserCreationForm
from django.contrib import admin
from django.contrib.admin import RelatedFieldListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.forms import ChoiceField, ModelForm, Select


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
        return (
            qs
            if request.user.is_superuser
            else qs.filter(scout__patrol__team=request.user.scout.patrol.team)
        )


admin.site.register(User, CustomUserAdmin)

FUNCTION_CHOICES = [
    (0, "Druh"),
    (1, "Podzastępowy"),
    (2, "Zastępowy"),
    (3, "Przyboczny"),
    (4, "Drużynowy"),
]


class ScoutAdminForm(ModelForm):
    class Meta:
        model = Scout
        fields = "__all__"
        widgets = {
            "user": Select(attrs={"style": "pointer-events: none;"}),
        }

    function = ChoiceField(choices=FUNCTION_CHOICES)


@admin.register(Scout)
class ScoutAdmin(admin.ModelAdmin):
    fields = (
        "user",
        "patrol",
        (
            "scout_rank",
            "instructor_rank",
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

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return "patrol__team", "patrol", "function", "scout_rank", "instructor_rank"
        return ("patrol", PatrolFilter), "scout_rank", "instructor_rank", "function"

    def user_nickname(self, obj):
        return obj.user.nickname

    def get_queryset(self, request):
        qs = super(ScoutAdmin, self).get_queryset(request)
        return (
            qs
            if request.user.is_superuser
            else qs.filter(patrol__team=request.user.scout.patrol.team)
        )

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            self.form = ScoutAdminForm

        return super(ScoutAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.user.is_superuser:
            obj.user.is_staff = True
        if obj.function == 4:
            obj.user.is_staff = True
            obj.user.user_permissions.clear()
            for perm in [
                "delete_task",
                "change_user",
                "delete_user",
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
                "delete_exam",
                "add_exam",
                "view_patrol",
                "view_team",
                "change_patrol",
            ]:
                obj.user.user_permissions.add(Permission.objects.get(codename=perm))
        elif obj.function >= 5:
            obj.user.is_staff = True
            obj.user.user_permissions.clear()
            for perm in [
                "delete_task",
                "change_user",
                "delete_user",
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
                "delete_exam",
                "add_exam",
                "view_patrol",
                "view_team",
                "change_patrol",
            ]:
                obj.user.user_permissions.add(Permission.objects.get(codename=perm))
        elif not obj.user.is_superuser:
            obj.user.is_staff = False
            obj.user.user_permissions.clear()

        obj.user.save()
        obj.save()


class PatrolFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        return field.get_choices(
            include_blank=False,
            limit_choices_to={
                "pk__in": request.user.scout.patrol.team.patrol_set.all()
            },
        )
