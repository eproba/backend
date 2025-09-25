from rest_framework import serializers


class ContactSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200)
    from_email = serializers.EmailField()
    message = serializers.CharField(max_length=1000)
    type = serializers.ChoiceField(
        choices=["bug", "general"], required=False, default="general"
    )

    def validate_subject(self, value):
        if not value.strip():
            raise serializers.ValidationError("Subject cannot be empty.")
        return value

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value
