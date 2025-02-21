from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Folder, Page


# Folder Admin with Tree Support
class FolderAdmin(TreeAdmin):
    form = movenodeform_factory(Folder)
    list_display = ("name", "owner", "visible", "created_at", "updated_at")
    list_filter = ("visible", "created_at", "updated_at")
    search_fields = ("name",)


# Page Admin
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "folder", "owner", "visible", "created_at", "updated_at")
    list_filter = ("visible", "created_at", "updated_at", "folder")
    search_fields = ("title", "content")
    ordering = ("title",)


# Register Folder with TreeAdmin
admin.site.register(Folder, FolderAdmin)
