from rest_framework import serializers

from .models import Scout, User


class ScoutSerializer(serializers.ModelSerializer):
    team = serializers.IntegerField(
        read_only=True, required=False, source="patrol.team.id"
    )
    patrol_name = serializers.CharField(
        read_only=True, required=False, source="patrol.name"
    )
    team_name = serializers.CharField(
        read_only=True, required=False, source="patrol.team.name"
    )

    class Meta:
        model = Scout
        fields = [
            "patrol",
            "patrol_name",
            "team",
            "team_name",
            "rank",
            "scout_rank",
            "instructor_rank",
            "function",
        ]


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
            "is_active",
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
            "is_active",
        ]

    def update(self, instance, validated_data):
        if "scout" in validated_data:
            scout_data = validated_data.pop("scout")
            for attr, value in scout_data.items():
                setattr(instance.scout, attr, value)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
