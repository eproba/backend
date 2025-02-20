from django.conf import settings


def google_auth_enabled(request):
    return {"google_auth_enabled": settings.GOOGLE_OAUTH_CLIENT_ID is not None}


def dev_mode(request):
    return {"dev_mode": settings.DEV}
