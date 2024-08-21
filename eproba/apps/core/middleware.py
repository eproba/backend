from constance import config
from django.http import JsonResponse

EXCLUDED_API_PATHS = [
    "api-config",
]


class APIMaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.lstrip("/")

        if (
            config.API_MAINTENANCE_MODE
            and path.startswith("api")
            and not any(
                path.startswith(f"api/{excluded_path}")
                for excluded_path in EXCLUDED_API_PATHS
            )
        ):
            return JsonResponse(
                {"error": "API is under maintenance, please try again later."},
                status=503,
            )

        return self.get_response(request)
