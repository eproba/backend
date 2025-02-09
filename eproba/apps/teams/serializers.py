from apps.users.serializers import UserSerializer
from rest_framework import serializers

from .models import District, Patrol, Team, TeamRequest


class PatrolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrol
        fields = ["id", "name", "team"]


class TeamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "short_name", "district", "is_verified"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]


class TeamSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()
    patrols = PatrolSerializer(many=True, source="patrol_set")

    class Meta:
        model = Team
        fields = ["id", "name", "short_name", "district", "is_verified", "patrols"]


class TeamRequestSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    created_by = UserSerializer()

    class Meta:
        model = TeamRequest
        fields = "__all__"
