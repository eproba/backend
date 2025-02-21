from django.urls import path

from . import views

app_name = "wiki"
urlpatterns = [
    path("", views.folder, name="index"),
    path("folder/<uuid:folder_id>/", views.folder, name="folder"),
    path("page/<uuid:page_id>/", views.page, name="page"),
    path("create-page/", views.folder, name="create_root_page"),
    path("create-page/<uuid:folder_id>/", views.folder, name="create_page"),
]
