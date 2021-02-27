from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import Scout, User
from apps.users.views import UserCreationForm
from django.contrib.auth.models import Group


class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    model = User
    list_display = (
        "email",
        "nickname",
        "is_staff",
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
    fieldsets = (
        (None, {"fields": ("email", "password", "nickname")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups")}),
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
                    "admin" "is_staff",
                    "admin" "is_superuser",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(User, CustomUserAdmin)


@admin.register(Scout)
class EventAdmin(admin.ModelAdmin):
    fields = (
        ("user"),
        ("team", "patrol"),
        ("rank", "is_patrol_leader", "is_team_leader"),
    )
    list_display = (
        "user",
        "user_nickname",
        "team",
        "patrol",
        "rank",
        "is_team_leader",
        "is_patrol_leader",
    )
    list_filter = ("team", "patrol", "rank", "is_team_leader", "is_patrol_leader")

    def user_nickname(self, obj):
        return obj.user.nickname
        
    def save_model(self, request, obj, form, change):
        if obj.is_team_leader:
            print(obj.user.is_staff)
            obj.user.is_staff = True
            print(obj.user.is_staff)
            try:
                rgroup = Group.objects.get(name='ZZ') 
                rgroup.user_set.remove(obj.user)
                group = Group.objects.get(name='leader') 
                group.user_set.add(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        elif obj.is_patrol_leader:
            print(obj.user.is_staff)
            obj.user.is_staff = True
            print(obj.user.is_staff)
            try:
                rgroup = Group.objects.get(name='leader') 
                rgroup.user_set.remove(obj.user)
                group = Group.objects.get(name='ZZ') 
                group.user_set.add(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        elif not obj.is_patrol_leader or not obj.is_team_leader:
            print(obj.user.is_staff)
            obj.user.is_staff = False
            print(obj.user.is_staff)
            try:
                group = Group.objects.get(name='leader') 
                group.user_set.remove(obj.user)
                group = Group.objects.get(name='ZZ') 
                group.user_set.remove(obj.user)
            except:
                pass
            obj.user.save()
            obj.save()
        else:
            obj.save()
