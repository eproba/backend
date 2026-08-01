from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View


def handler404(request, exception):
    return JsonResponse({"error": "Not found"}, status=404)


def handler500(request):
    return JsonResponse({"error": "Internal server error"}, status=500)


class RootView(View):
    """Root endpoint to inform users this is an API backend."""

    def get(self, request):
        context = {
            "api_docs_url": reverse("scalar-ui"),
            "api_root_url": "/api/",
            "show_notice": not settings.DEBUG,
        }
        return render(request, "core/root.html", context)
