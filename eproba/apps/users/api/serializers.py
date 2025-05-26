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
    gender = serializers.CharField(
        read_only=True, required=False, source="gender_string"
    )
    name = serializers.CharField(read_only=True, required=False, source="full_name")
    has_password = serializers.BooleanField(
        read_only=True, required=False, source="has_usable_password"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "name",
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
            "has_password",
            "is_staff",
            "is_superuser",
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
    gender = serializers.CharField(
        read_only=True, required=False, source="gender_string"
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
            "is_staff",
            "is_superuser",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False)
    new_password = serializers.CharField(required=True)

    def validate(self, data):
        user = self.context["request"].user

        if user.has_usable_password():
            if not data.get("old_password"):
                raise serializers.ValidationError(
                    {"old_password": "Obecne hasło jest wymagane"}
                )

            if not user.check_password(data.get("old_password")):
                raise serializers.ValidationError({"old_password": "Niepoprawne hasło"})

        return data
