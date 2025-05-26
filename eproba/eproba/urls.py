"""eproba URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from apps.blog.api.views import PostViewSet
from apps.blog.sitemaps import PostSitemap
from apps.core.views import FrontPageView, contactView, fcm_sw, site_management
from apps.teams.api.views import (
    DistrictViewSet,
    PatrolViewSet,
    TeamRequestViewSet,
    TeamViewSet,
)
from apps.users.api.views import UserInfo, UserViewSet
from apps.users.views import (
    change_password,
    delete_account,
    edit_profile,
    finish_signup,
    google_auth_receiver,
    password_reset_complete,
    password_reset_done,
    select_patrol,
    send_verification_email,
    set_password,
    signup,
    verify_email,
    view_profile,
)
from apps.worksheets.api.views import (
    SubmitTask,
    TaskActionView,
    TaskDetails,
    TasksToBeChecked,
    TemplateWorksheetViewSet,
    UnsubmitTask,
    WorksheetViewSet,
)
from django.conf import settings

# from apps.users.views.login_hub import login_from_hub, login_hub
from django.contrib import admin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from oauth2_provider.urls import app_name as oauth2_app_name
from oauth2_provider.urls import base_urlpatterns as oauth2_base_urlpatterns
from oauth2_provider.urls import oidc_urlpatterns
from rest_framework import routers

from .sitemaps import Sitemap
from .utils import (
    ApiConfigView,
)

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"

# Routers provide a way of automatically determining the URL conf.
api = routers.DefaultRouter()
api.register(r"fcm/devices", FCMDeviceAuthorizedViewSet, "fcm_devices")
api.register(r"worksheets", WorksheetViewSet, "api-worksheets")
api.register(r"templates", TemplateWorksheetViewSet, "api-templates")
api.register(r"users", UserViewSet, "api-users")
api.register(r"districts", DistrictViewSet, "api-districts")
api.register(r"teams", TeamViewSet, "api-teams")
api.register(r"patrols", PatrolViewSet, "api-patrols")
api.register(r"team-requests", TeamRequestViewSet, basename="team-requests")
api.register("news", PostViewSet, basename="news")

sitemaps = {
    "posts": PostSitemap,
    "static": Sitemap,
}
admin.site.site_title = "EPRÓBA"
admin.site.site_header = "Panel administratora" + " - DEV" if settings.DEV else ""
urlpatterns = [
    path("", FrontPageView.as_view(), name="frontpage"),
    path("firebase-messaging-sw.js", fcm_sw, name="fcm_sw"),
    path(
        "about/", TemplateView.as_view(template_name="sites/about.html"), name="about"
    ),
    path(
        "gdpr/",
        TemplateView.as_view(template_name="sites/gdpr.html"),
        name="gdpr",
    ),
    path(
        "privacy-policy/",
        TemplateView.as_view(template_name="sites/privacy_policy.html"),
        name="privacy-policy",
    ),
    path(
        "terms-of-service/",
        TemplateView.as_view(template_name="sites/terms_of_service.html"),
        name="terms",
    ),
    path("admin/", admin.site.urls, name="admin"),
    path("api/", include(api.urls)),
    path("api/api-config/", ApiConfigView.as_view()),
    path("api/user/", UserInfo.as_view({"get": "list"})),
    path(
        "api/worksheets/<uuid:worksheet_id>/task/<uuid:id>/",  # Outdated URL
        TaskDetails.as_view({"get": "retrieve", "patch": "partial_update"}),
    ),
    path(
        "api/worksheets/<uuid:worksheet_id>/tasks/<uuid:id>/",
        TaskDetails.as_view({"get": "retrieve", "patch": "partial_update"}),
    ),
    path("api/worksheets/tasks/tbc/", TasksToBeChecked.as_view()),
    path(
        "api/worksheets/<uuid:worksheet_id>/task/<uuid:id>/submit",
        SubmitTask.as_view(),  # Outdated URL
    ),
    path(
        "api/worksheets/<uuid:worksheet_id>/task/<uuid:id>/unsubmit",  # Outdated URL
        UnsubmitTask.as_view(),
    ),
    path(
        "api/worksheets/<uuid:worksheet_id>/tasks/<uuid:id>/<str:action>/",
        TaskActionView.as_view(),
    ),
    path("contact/", contactView, name="contact"),
    path("worksheets/", include("apps.worksheets.urls")),
    path(
        "login/",
        LoginView.as_view(
            template_name="users/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    # path("lh/", login_hub),
    # path("_login/<uuid:user_id>/", login_from_hub),
    path("news/", include("apps.blog.urls")),
    path(
        "password-reset/",
        PasswordResetView.as_view(template_name="users/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password-reset-complete/",
        password_reset_complete,
        name="password_reset_complete",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path("password-reset-done/", password_reset_done, name="password_reset_done"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("profile/change-password/", change_password, name="change_password"),
    path("profile/set-password/", set_password, name="set_password"),
    path("profile/view/", view_profile, name="view_profile", kwargs={"user_id": None}),
    path("profile/view/<uuid:user_id>/", view_profile, name="view_profile"),
    path("profile/delete/", delete_account, name="delete_account"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("signup/", signup, name="signup"),
    path("signup/finalize/", finish_signup, name="finish_signup"),
    path("team/", include("apps.teams.urls")),
    path(
        "oauth2/",
        include(
            (oauth2_base_urlpatterns + oidc_urlpatterns, oauth2_app_name),
            namespace="oauth2_provider",
        ),
    ),
    path("site-management/", site_management, name="site_management"),
    path(
        "app-ads.txt",
        RedirectView.as_view(url=staticfiles_storage.url("app-ads.txt")),
    ),
    path(
        "ads.txt",
        RedirectView.as_view(url=staticfiles_storage.url("ads.txt")),
    ),
    path(
        "google-auth-receiver/",
        google_auth_receiver,
        name="google_auth_receiver",
    ),
    path("select-patrol/", select_patrol, name="select_patrol"),
    path(
        "send-verification-email/",
        send_verification_email,
        name="send_verification_email",
    ),
    path(
        "verify-email/<uuid:user_id>/<uuid:token>/", verify_email, name="verify_email"
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("tinymce/", include("tinymce.urls")),
    path("wiki/", include("apps.wiki.urls")),
]
