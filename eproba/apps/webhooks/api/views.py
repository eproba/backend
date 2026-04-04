from apps.core.api.permissions import TokenHasRequiredScope
from apps.webhooks.models import Webhook
from apps.webhooks.serializers import WebhookSerializer
from rest_framework import permissions, viewsets


class WebhookViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated, TokenHasRequiredScope]
    required_scopes = ["webhooks"]

    def get_queryset(self):
        return Webhook.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
