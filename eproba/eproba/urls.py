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

from apps.blog.sitemaps import PostSitemap
from apps.core.views import FrontPageView, contactView, fcm_sw, site_management
from apps.users.views import (
    change_password,
    duplicated_accounts,
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
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from oauth2_provider.urls import app_name as oauth2_app_name
from oauth2_provider.urls import base_urlpatterns as oauth2_base_urlpatterns
from rest_framework import routers

from .sitemaps import Sitemap
from .utils import (
    ApiConfigView,
    PatrolViewSet,
    SubmitTask,
    TaskDetails,
    TasksToBeChecked,
    TeamViewSet,
    UnsubmitTask,
    UserInfo,
    UserViewSet,
    WorksheetViewSet,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"

# Routers provide a way of automatically determining the URL conf.
api = routers.DefaultRouter()
api.register(r"fcm/devices", FCMDeviceAuthorizedViewSet, "fcm_devices")
api.register(r"worksheets", WorksheetViewSet, "api-worksheets")
api.register(r"users", UserViewSet, "api-users")
api.register(r"teams", TeamViewSet, "api-teams")
api.register(r"patrols", PatrolViewSet, "api-patrols")

sitemaps = {
    "posts": PostSitemap,
    "static": Sitemap,
}
admin.site.site_title = "EPRÓBA"
admin.site.site_header = "Panel administratora"
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
        "api/worksheets/<uuid:worksheet_id>/task/<uuid:id>/",
        TaskDetails.as_view({"get": "retrieve", "patch": "partial_update"}),
    ),
    path("api/worksheets/tasks/tbc/", TasksToBeChecked.as_view()),
    path(
        "api/worksheets/<uuid:worksheet_id>/task/<uuid:id>/submit", SubmitTask.as_view()
    ),
    path(
        "api/worksheets/<uuid:worksheet_id>/task/<uuid:id>/unsubmit",
        UnsubmitTask.as_view(),
    ),
    path("contact/", contactView, name="contact"),
    path("worksheets/", include("apps.worksheets.urls")),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
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
    path("profile/edit/<uuid:user_id>/", edit_profile, name="edit_profile"),
    path(
        "profile/edit/<uuid:user_id>/password/", change_password, name="change_password"
    ),
    path("profile/set/<uuid:user_id>/password/", set_password, name="set_password"),
    path("profile/view/", view_profile, name="view_profile", kwargs={"user_id": None}),
    path("profile/view/<uuid:user_id>/", view_profile, name="view_profile"),
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
            (oauth2_base_urlpatterns, oauth2_app_name), namespace="oauth2_provider"
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
        "duplicated-accounts/<uuid:user_id_1>/<uuid:user_id_2>/",
        duplicated_accounts,
        name="duplicated_accounts",
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
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]