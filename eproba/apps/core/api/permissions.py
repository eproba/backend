from rest_framework import permissions


class TokenHasRequiredScope(permissions.BasePermission):
    """
    Checks if an OAuth2 token has all scopes listed in view.required_scopes.
    If the request is not authenticated via an OAuth2 token (e.g. Session auth),
    it allows access automatically so IsAuthenticated can handle the base auth.
    """

    def has_permission(self, request, view):
        token = getattr(request, "auth", None)
        if not token:
            return True

        required_scopes = getattr(view, "required_scopes", [])

        if hasattr(token, "scope"):
            token_scopes = token.scope.split()
            for scope in required_scopes:
                if scope not in token_scopes:
                    return False
            return True
        return False
