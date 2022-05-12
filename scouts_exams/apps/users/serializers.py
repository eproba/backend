from rest_framework import serializers

from .models import Scout, User


class ScoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scout
        fields = ["patrol", "rank", "function"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    scout = ScoutSerializer()

    class Meta:
        model = User
        fields = [
            "url",
            "nickname",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "scout",
        ]
