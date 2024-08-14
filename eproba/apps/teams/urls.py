from django.urls import path

from . import views

app_name = "teams"
urlpatterns = [
    path("", views.view_teams, name="view_teams"),
    path("patrol/<int:patrol_id>/", views.view_patrol, name="view_patrol"),
    path("user/<int:user_id>/", views.manage_user, name="manage_user"),
]
