from django.urls import include, path
from rest_framework import routers

from apps.webhooks.api.views import WebhookViewSet

router = routers.DefaultRouter()
router.register(r"", WebhookViewSet, basename="webhooks")

urlpatterns = [
    path("", include(router.urls)),
]
