from rest_framework import serializers

from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = (
            "id",
            "user",
            "url",
            "secret",
            "events",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "secret", "created_at", "updated_at")

    def validate_events(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Events must be a list of strings.")
        valid_events = {"task.status_changed", "task.sent_to_review"}
        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(
                    f"Invalid event: {event}. Valid events: {', '.join(valid_events)}"
                )
        return value
