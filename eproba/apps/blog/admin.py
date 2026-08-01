from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Post


class PostAdmin(ModelAdmin):
    list_display = ("title", "slug", "status", "created_on")
    list_filter = ("status",)
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Post, PostAdmin)
