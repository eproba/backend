from django.conf import settings


def google_auth_enabled(request):
    return {"google_auth_enabled": settings.GOOGLE_OAUTH_CLIENT_ID is not None}
