from django.urls import path

from . import views

app_name = "exam"
urlpatterns = [
    path("", views.view_exams, name="exam"),
    path("s/<str:hex>/", views.view_shared_exams, name="exam_detail"),
    path("archive", views.archive, name="archive"),
    path("create", views.create_exam, name="create_exam"),
    path("edit/<int:exam_id>/", views.edit_exam, name="edit_exam"),
    path("manage", views.manage_exams, name="manage_exams"),
    path("print/<str:hex>", views.print_exam, name="print_exam"),
    path("share/view/<str:hex>", views.view_shared_exams, name="view_shared_exams"),
    path("tasks/check", views.check_tasks, name="check_tasks"),
    path("templates", views.templates, name="templates"),
    path(
        "<int:exam_id>/task/<int:task_id>/accept",
        views.accept_task,
        name="accept_task",
    ),
    path(
        "<int:exam_id>/task/<int:task_id>/reject", views.reject_task, name="reject_task"
    ),
    path("<int:exam_id>/tasks/sent", views.sent_tasks, name="sent_tasks"),
    path("<int:exam_id>/task/submit", views.submit_task, name="submit_task"),
    path(
        "<int:exam_id>/<int:task_id>/task/unsubmit",
        views.unsubmit_task,
        name="unsubmit_task",
    ),
    path(
        "<int:exam_id>/task/<int:task_id>/force/accept",
        views.force_accept_task,
        name="force_accept_task",
    ),
    path(
        "<int:exam_id>/task/<int:task_id>/force/reject",
        views.force_reject_task,
        name="force_reject_task",
    ),
]
