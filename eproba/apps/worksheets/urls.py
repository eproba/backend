from django.urls import path

from . import views

app_name = "worksheets"
urlpatterns = [
    path("", views.view_worksheets, name="worksheets"),
    path("s/<uuid:id>/", views.view_shared_worksheet, name="worksheet_detail"),
    path("archive/", views.archive, name="archive"),
    path("create/", views.create_worksheet, name="create_worksheet"),
    path("create-template/", views.create_template, name="create_template"),
    path("edit/<uuid:worksheet_id>/", views.edit_worksheet, name="edit_worksheet"),
    path(
        "edit-template/<uuid:worksheet_id>/", views.edit_template, name="edit_template"
    ),
    path("manage/", views.manage_worksheets, name="manage_worksheets"),
    path("print/<uuid:id>/", views.print_worksheet, name="print_worksheet"),
    path(
        "print-template/<uuid:id>/",
        views.print_worksheet_template,
        name="print_worksheet_template",
    ),
    path(
        "share/view/<uuid:id>/",
        views.view_shared_worksheet,
        name="view_shared_worksheets",
    ),
    path("tasks/check/", views.check_tasks, name="check_tasks"),
    path("templates/", views.templates, name="templates"),
    path("<uuid:id>/print/", views.print_worksheet, name="print_worksheet"),
    path(
        "<uuid:worksheet_id>/task/<uuid:task_id>/accept/",
        views.accept_task,
        name="accept_task",
    ),
    path(
        "<uuid:worksheet_id>/task/<uuid:task_id>/reject/",
        views.reject_task,
        name="reject_task",
    ),
    path("<uuid:worksheet_id>/tasks/sent/", views.sent_tasks, name="sent_tasks"),
    path("<uuid:worksheet_id>/task/submit/", views.submit_task, name="submit_task"),
    path(
        "<uuid:worksheet_id>/<uuid:task_id>/task/unsubmit/",
        views.unsubmit_task,
        name="unsubmit_task",
    ),
    path("export/", views.export, name="export"),
    path(
        "export/<uuid:worksheet_id>/", views.export_worksheet, name="export_worksheet"
    ),
]
