from django.urls import path

from . import views

app_name = "exam"
urlpatterns = [
    path("", views.view_exams, name="exam"),
    path("archive", views.archive, name="archive"),
    path("create", views.create_exam, name="create_exam"),
    path("manage", views.manage_exams, name="manage_exams"),
    path("print/<str:hex>", views.print_exam, name="print_exam"),
    path("share/view/<str:hex>", views.view_shared_exams, name="view_shared_exams"),
    path("tasks/check", views.check_tasks, name="check_tasks"),
    path("templates", views.templates, name="templates"),
    path(
        "<int:exam_id>/<int:task_id>/task/accept",
        views.accept_task,
        name="accept_task",
    ),
    path(
        "<int:exam_id>/<int:task_id>/task/refuse", views.refuse_task, name="refuse_task"
    ),
    path("<int:exam_id>/tasks/sent", views.sent_tasks, name="sent_tasks"),
    path("<int:exam_id>/task/submit", views.submit_task, name="submit_task"),
    path(
        "<int:exam_id>/<int:task_id>/task/unsubmit",
        views.unsubmit_task,
        name="unsubmit_task",
    ),
    path(
        "<int:exam_id>/<int:task_id>/task/force/accept",
        views.force_accept_task,
        name="force_accept_task",
    ),
    path(
        "<int:exam_id>/<int:task_id>/task/force/refuse",
        views.force_refuse_task,
        name="force_refuse_task",
    ),
]
