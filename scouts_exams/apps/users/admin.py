from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from apps.users.models import Scout, User
from apps.users.views import UserCreationForm


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    model = User
    list_display = (
        "email",
        "nickname",
        "is_superuser",
        "is_active",
    )
    list_filter = (
        "email",
        "nickname",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    fieldsets = ((None, {"fields": ("email", "password", "nickname")}),)
    super_fieldsets = (
        (None, {"fields": ("email", "password", "nickname")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "is_superuser", "groups")},
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
            return qs.filter(scout__team=request.user.scout.team)
        else:
            return qs


admin.site.register(User, CustomUserAdmin)


@admin.register(Scout)
class EventAdmin(admin.ModelAdmin):
    fields = (
        ("user"),
        ("team", "patrol"),
        ("rank"),
    )
    leader_fields = (
        ("user"),
        ("team", "patrol"),
        ("rank", "is_patrol_leader", "is_second_team_leader"),
    )
    super_fields = (
        ("user"),
        ("team", "patrol"),
        ("rank", "is_patrol_leader", "is_second_team_leader", "is_team_leader"),
    )
    list_display = (
        "user",
        "user_nickname",
        "team",
        "patrol",
        "rank",
        "is_team_leader",
        "is_second_team_leader",
        "is_patrol_leader",
    )
    list_filter = (
        "team",
        "patrol",
        "rank",
        "is_team_leader",
        "is_second_team_leader",
        "is_patrol_leader",
    )

    def user_nickname(self, obj):
        return obj.user.nickname

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            self.fields = self.super_fields
        elif request.user.scout.is_team_leader:
            self.fields = self.leader_fields

        return super(EventAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(EventAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(team=request.user.scout.team)
        else:
            return qs

    def save_model(self, request, obj, form, change):
        if obj.is_team_leader:
            obj.user.is_staff = True
            try:
                rgroup = Group.objects.get(name="ZZ")
                rgroup.user_set.remove(obj.user)
                rgroup = Group.objects.get(name="second_leader")
                rgroup.user_set.remove(obj.user)
                group = Group.objects.get(name="leader")
                group.user_set.add(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        elif obj.is_second_team_leader:
            obj.user.is_staff = True
            try:
                rgroup = Group.objects.get(name="ZZ")
                rgroup.user_set.remove(obj.user)
                rgroup = Group.objects.get(name="leader")
                rgroup.user_set.remove(obj.user)
                group = Group.objects.get(name="second_leader")
                group.user_set.add(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        elif obj.is_patrol_leader:
            obj.user.is_staff = True
            try:
                rgroup = Group.objects.get(name="leader")
                rgroup.user_set.remove(obj.user)
                rgroup = Group.objects.get(name="second_leader")
                rgroup.user_set.remove(obj.user)
                group = Group.objects.get(name="ZZ")
                group.user_set.add(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        elif (
            not obj.is_patrol_leader
            or not obj.is_team_leader
            or not obj.is_second_team_leader
        ):
            if not obj.user.is_superuser:
                obj.user.is_staff = False
            try:
                group = Group.objects.get(name="leader")
                group.user_set.remove(obj.user)
                group = Group.objects.get(name="second_leader")
                group.user_set.remove(obj.user)
                group = Group.objects.get(name="ZZ")
                group.user_set.remove(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        else:
            obj.save()
