from django.urls import path

from . import views

app_name = "wiki"
urlpatterns = [
    path("", views.folder, name="index"),
    path("folder/<uuid:folder_id>/", views.folder, name="folder"),
    path(
        "folder/<uuid:folder_id>/create-folder/",
        views.create_folder,
        name="create_folder",
    ),
    path("folder/<uuid:folder_id>/create-page/", views.create_page, name="create_page"),
    path("page/<uuid:page_id>/", views.page, name="page"),
    path("create-folder/", views.create_folder, name="create_root_folder"),
    path("create-page/", views.create_page, name="create_root_page"),
    path("edit-folder/<uuid:folder_id>/", views.edit_folder, name="edit_folder"),
    path("edit-page/<uuid:page_id>/", views.edit_page, name="edit_page"),
    path("init-wiki/", views.init_wiki, name="init_wiki"),
]
