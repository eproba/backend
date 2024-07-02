from apps.users.models import EndMessage
from constance import config
from django.http import JsonResponse
from django.shortcuts import render

EXCLUDED_END_PATHS = [
    "/robots.txt",
    "/app-ads.txt",
    "/ads.txt",
    "/sitemap.xml",
    "/privacy-policy",
    "/terms-of-service",
    "/gdpr",
    "/site-management",
    "/login",
    "/password-reset",
    "/password-reset-done",
    "/oauth2/authorize",
    "/accounts/google/login",
    "/accounts/google/login/callback",
    "/accounts/facebook/login",
    "/accounts/facebook/login/callback",
    "/static/images/icons/favicon.svg",
    "/api/app_config",
]


class TheEndMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        path = request.path_info

        if config.THE_END and path.removesuffix("/") not in EXCLUDED_END_PATHS:
            if path.startswith("/api"):
                return JsonResponse({"error": "The end"})
            if request.user.is_authenticated:
                end_messages = []
                for message in EndMessage.objects.all():
                    if message.target_type == "all":
                        end_messages.append(message.message)
                    elif message.target_type == "users":
                        if request.user in message.targets.all():
                            end_messages.append(message.message)
                    elif message.target_type == "users_exclude":
                        if request.user not in message.targets.all():
                            end_messages.append(message.message)
                return render(
                    request, "sites/the_end.html", {"end_messages": end_messages}
                )
            return render(request, "sites/the_end.html")

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
