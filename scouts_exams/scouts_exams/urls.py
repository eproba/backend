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
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.views import IssueContactView, contactView, frontpage
from apps.users.views import (
    change_password, disconect_socials, edit_profile, finish_signup,
    set_password, signup, view_profile,
)

handler404 = TemplateView.as_view(template_name="sites/404.html")
urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("exam/", include("apps.exam.urls")),
    path(
        "about/", TemplateView.as_view(template_name="sites/about.html"), name="about"
    ),
    path("contact/", contactView, name="contact"),
    path("contact/issue", IssueContactView, name="issue_contact"),
    path("", frontpage, name="frontpage"),
    path(
        "accounts/social/connections/",
        view_profile,
        name="socialaccount_connections",
        kwargs={"user_id": None},
    ),
    path("account/socials/disconect", disconect_socials, name="disconect_socials"),
    path("accounts/", include("allauth.urls")),
    path("signup/", signup, name="signup"),
    path("signup/finish", finish_signup, name="finish_signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("profile/view/", view_profile, name="view_profile", kwargs={"user_id": None}),
    path("profile/view/<int:user_id>", view_profile, name="view_profile"),
    path("profile/edit/<int:user_id>", edit_profile, name="edit_profile"),
    path(
        "profile/edit/<int:user_id>/password", change_password, name="change_password"
    ),
    path("profile/set/<int:user_id>/password", set_password, name="set_password"),
]
