from rest_framework import serializers

from .models import Patrol, Team


class PatrolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrol
        fields = ["id", "name", "team"]


class TeamSerializer(serializers.ModelSerializer):
    patrols = PatrolSerializer(many=True, source="patrol_set")

    class Meta:
        model = Team
        fields = ["id", "name", "short_name", "patrols"]
