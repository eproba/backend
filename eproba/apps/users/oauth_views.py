from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.views import AuthorizationView as BaseAuthorizationView


@method_decorator(never_cache, name="dispatch")
class AuthorizationView(BaseAuthorizationView):
    """
    Custom OAuth2 Authorization view that checks for existing authorizations
    """

    template_name = "oauth2_provider/authorize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if user has already authorized this application
        if self.request.user.is_authenticated:
            application = self.get_application()
            if application:
                # Check for existing valid access tokens
                existing_tokens = (
                    AccessToken.objects.filter(
                        user=self.request.user,
                        application=application,
                    )
                    .exclude(token__isnull=True)
                    .exclude(token__exact="")
                )

                if existing_tokens.exists():
                    context["user_already_authorized"] = True
                    # Get the scopes from the most recent token
                    latest_token = existing_tokens.order_by("-created").first()
                    if latest_token and latest_token.scope:
                        context["previous_scopes"] = latest_token.scope.split()
                        all_scopes = get_scopes_backend().get_all_scopes()
                        context["previous_scopes_descriptions"] = [
                            all_scopes.get(scope, scope)
                            for scope in context["previous_scopes"]
                        ]
                    else:
                        context["previous_scopes"] = []
                        context["previous_scopes_descriptions"] = []

                    # Check for new scopes being requested
                    requested_scopes = self.request.GET.get("scope", "").split()
                    if requested_scopes:
                        previous_scopes = set(context.get("previous_scopes", []))
                        new_scopes = [
                            scope
                            for scope in requested_scopes
                            if scope not in previous_scopes
                        ]

                        if new_scopes:
                            context["new_scopes"] = new_scopes
                            all_scopes = get_scopes_backend().get_all_scopes()
                            context["new_scopes_descriptions"] = [
                                all_scopes.get(scope, scope) for scope in new_scopes
                            ]
                        else:
                            context["new_scopes"] = []
                            context["new_scopes_descriptions"] = []
                    else:
                        context["new_scopes"] = []
                        context["new_scopes_descriptions"] = []
                else:
                    context["user_already_authorized"] = False
            else:
                context["user_already_authorized"] = False
        else:
            context["user_already_authorized"] = False

        return context

    def get_application(self):
        """Get the application object from the request"""
        try:
            client_id = self.request.GET.get("client_id")
            if client_id:
                return Application.objects.get(client_id=client_id)
        except Application.DoesNotExist:
            pass
        return None
