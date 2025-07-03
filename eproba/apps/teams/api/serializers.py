from apps.teams.models import District, Patrol, Team, TeamRequest
from apps.users.api.serializers import UserSerializer
from rest_framework import serializers


class PatrolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrol
        fields = ["id", "name", "team"]


class TeamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "short_name", "district", "is_verified", "organization"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]


class TeamSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()
    patrols = PatrolSerializer(many=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "short_name",
            "district",
            "is_verified",
            "patrols",
            "organization",
        ]


class TeamRequestSerializer(serializers.ModelSerializer):
    # Read-only fields for existing requests
    team = TeamSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    # Write-only fields for creation
    team_name = serializers.CharField(
        max_length=200, write_only=True, required=False, help_text="Full team name"
    )
    team_short_name = serializers.CharField(
        max_length=20, write_only=True, required=False, help_text="Short team name"
    )
    district = serializers.UUIDField(
        write_only=True, required=False, help_text="District UUID"
    )
    organization = serializers.IntegerField(
        write_only=True,
        required=False,
        help_text="0 for Male Scouts, 1 for Female Scouts",
    )
    patrols = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        help_text="List of patrol names",
    )
    user_patrol = serializers.CharField(
        max_length=100,
        write_only=True,
        required=False,
        help_text="Which patrol the user belongs to",
    )

    class Meta:
        model = TeamRequest
        fields = [
            # Read-only fields
            "id",
            "team",
            "created_by",
            "accepted_by",
            "status",
            "created_at",
            "notes",
            # Read-write field
            "function_level",
            # Write-only fields for creation
            "team_name",
            "team_short_name",
            "district",
            "organization",
            "patrols",
            "user_patrol",
        ]
        read_only_fields = [
            "id",
            "team",
            "created_by",
            "accepted_by",
            "status",
            "created_at",
            "notes",
        ]

    def validate_district(self, value):
        if value is None:
            return value
        try:
            District.objects.get(id=value)
        except District.DoesNotExist:
            raise serializers.ValidationError("District does not exist")
        return value

    def validate_organization(self, value):
        if value is not None and value not in [0, 1]:
            raise serializers.ValidationError("Organization must be 0 or 1")
        return value

    def validate_patrols(self, value):
        if value:
            # Remove empty strings and strip whitespace
            cleaned_patrols = [name.strip() for name in value if name.strip()]
            if not cleaned_patrols:
                raise serializers.ValidationError(
                    "At least one non-empty patrol name is required"
                )
            return cleaned_patrols
        return value

    def validate(self, attrs):
        # Only validate creation fields if we're creating
        if self.instance is None:  # Creating new instance
            required_fields = [
                "team_name",
                "team_short_name",
                "district",
                "organization",
                "patrols",
                "function_level",
            ]
            for field in required_fields:
                if field not in attrs or attrs[field] is None:
                    raise serializers.ValidationError(
                        f"{field} is required for creation"
                    )
        return attrs

    def create(self, validated_data):
        # Extract team and patrol data
        team_data = {
            "name": validated_data.pop("team_name"),
            "short_name": validated_data.pop("team_short_name"),
            "district_id": validated_data.pop("district"),
            "organization": validated_data.pop("organization"),
            "is_verified": False,
        }
        patrols = validated_data.pop("patrols")
        user_patrol = validated_data.pop("user_patrol", None)

        # Create the team
        team = Team.objects.create(**team_data)

        # Create patrols
        for patrol_name in patrols:
            team.patrols.create(name=patrol_name)

        # Set user's patrol and function
        user = self.context["request"].user
        if user_patrol:
            user.patrol = (
                team.patrols.filter(name=user_patrol).first() or team.patrols.first()
            )
        else:
            user.patrol = team.patrols.first()
        user.function = 0
        user.save()

        # Create team request
        team_request = TeamRequest.objects.create(
            created_by=user, team=team, function_level=validated_data["function_level"]
        )

        return team_request
