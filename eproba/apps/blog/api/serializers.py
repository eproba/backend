from apps.users.api.serializers import UserSerializer
from rest_framework import serializers

from ..models import Post


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)
    status_id = serializers.IntegerField(source="status", write_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "updated_on",
            "content",
            "created_on",
            "status",
            "status_id",
            "authorized_only",
            "minimum_function",
            "pinned",
            "priority",
            "hidden",
        ]
        read_only_fields = ["id", "created_on", "updated_on"]
