from rest_framework import serializers

from .models import Scout, User


class ScoutSerializer(serializers.ModelSerializer):
    team = serializers.IntegerField(required=False, source="patrol.team.id")
    patrol_name = serializers.CharField(required=False, source="patrol.name")
    team_name = serializers.CharField(required=False, source="patrol.team.name")

    class Meta:
        model = Scout
        fields = ["patrol", "patrol_name", "team", "team_name", "rank", "function"]


class UserSerializer(serializers.ModelSerializer):
    scout = ScoutSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "scout",
        ]


class PublicUserSerializer(serializers.HyperlinkedModelSerializer):
    scout = ScoutSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "scout",
        ]
