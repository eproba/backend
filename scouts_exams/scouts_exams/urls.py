"""scouts_exams URL Configuration

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
from apps.core.views import IssueContactView, contactView, fcm_sw, frontpage
from apps.users.views import (
    change_password,
    disconect_socials,
    edit_profile,
    finish_signup,
    password_reset_complete,
    password_reset_done,
    set_password,
    signup,
    view_profile,
)
from django.contrib import admin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework import routers

from .sitemaps import Sitemap
from .utils import (
    ExamDetails,
    ExamList,
    UserDetails,
    UserExamDetails,
    UserExamList,
    UserInfo,
    UserList,
)

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"

# Routers provide a way of automatically determining the URL conf.
api = routers.DefaultRouter()
api.register(r"fcm/devices", FCMDeviceAuthorizedViewSet, "fcm_devices")

sitemaps = {
    "posts": PostSitemap,
    "static": Sitemap,
}
admin.site.site_title = "EPRÓBA"
admin.site.site_header = "Panel administratora"
urlpatterns = [
    path("", frontpage, name="frontpage"),
    path("firebase-messaging-sw.js", fcm_sw, name="fcm_sw"),
    path(
        "about/", TemplateView.as_view(template_name="sites/about.html"), name="about"
    ),
    path("accounts/", include("allauth.urls")),
    path("account/disconect/<provider>", disconect_socials, name="disconect_socials"),
    path("admin/", admin.site.urls, name="admin"),
    path("api/", include(api.urls)),
    path("api/user/", UserInfo.as_view({"get": "list"})),
    path("api/exams/", UserExamList.as_view({"get": "list"})),
    path("api/exams/<pk>/", UserExamDetails.as_view()),
    path("api/all/exams/", ExamList.as_view({"get": "list"})),
    path("api/all/exams/<pk>/", ExamDetails.as_view()),
    path("api/all/users/", UserList.as_view()),
    path("api/all/users/<pk>/", UserDetails.as_view(), name="user-detail"),
    path("contact/", contactView, name="contact"),
    path("contact/issue", IssueContactView, name="issue_contact"),
    path("exam/", include("apps.exam.urls")),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
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
    path("profile/edit/<int:user_id>", edit_profile, name="edit_profile"),
    path(
        "profile/edit/<int:user_id>/password", change_password, name="change_password"
    ),
    path("profile/set/<int:user_id>/password", set_password, name="set_password"),
    path("profile/view/", view_profile, name="view_profile", kwargs={"user_id": None}),
    path("profile/view/<int:user_id>", view_profile, name="view_profile"),
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
    path("signup/finish", finish_signup, name="finish_signup"),
]
