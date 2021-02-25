from django.urls import path

from . import views

app_name = "exam"
urlpatterns = [
    path("", views.view_exams, name="exam"),
    path(
        "<int:user_id>/<int:exam_id>/task/submit", views.sumbit_task, name="submit_task"
    ),
    path(
        "<int:user_id>/<int:exam_id>/<int:task_id>/task/unsubmit",
        views.unsubmit_task,
        name="unsubmit_task",
    ),
    path("<int:user_id>/<int:exam_id>/tasks/sent", views.sent_tasks, name="sent_tasks"),
]
