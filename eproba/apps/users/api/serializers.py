from apps.users.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    team = serializers.UUIDField(
        read_only=True, required=False, source="patrol.team.id"
    )
    patrol_name = serializers.CharField(
        read_only=True, required=False, source="patrol.name"
    )
    team_name = serializers.CharField(
        read_only=True, required=False, source="patrol.team.name"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "email",
            "email_verified",
            "is_active",
            "patrol",
            "patrol_name",
            "team",
            "team_name",
            "rank",
            "scout_rank",
            "instructor_rank",
            "function",
            "gender",
        ]


class PublicUserSerializer(serializers.ModelSerializer):

    team = serializers.UUIDField(
        read_only=True, required=False, source="patrol.team.id"
    )
    patrol_name = serializers.CharField(
        read_only=True, required=False, source="patrol.name"
    )
    team_name = serializers.CharField(
        read_only=True, required=False, source="patrol.team.name"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "email_verified",
            "is_active",
            "patrol",
            "patrol_name",
            "team",
            "team_name",
            "rank",
            "scout_rank",
            "instructor_rank",
            "function",
            "gender",
        ]
