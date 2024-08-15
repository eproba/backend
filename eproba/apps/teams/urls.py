from django.urls import path

from . import views

app_name = "teams"
urlpatterns = [
    path("", views.view_teams, name="view_teams"),
    path("patrol/<uuid:patrol_id>/", views.view_patrol, name="view_patrol"),
    path("user/<uuid:user_id>/", views.manage_user, name="manage_user"),
]
