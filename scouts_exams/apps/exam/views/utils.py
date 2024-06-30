def prepare_exam(exam):
    _all = 0
    _done = 0
    exam.show_submit_task_button = False
    exam.show_sent_tasks_button = False
    exam.show_description_column = False
    for task in exam.tasks.all():
        _all += 1
        if task.status == 2:
            _done += 1
        elif task.status in [0, 3]:
            exam.show_submit_task_button = True
        elif task.status == 1:
            exam.show_sent_tasks_button = True
        if task.description != "":
            exam.show_description_column = True
    if _all != 0:
        percent = int(round(_done / _all, 2) * 100)
        exam.percent = f"{percent}%"
    else:
        exam.percent = "Nie masz jeszcze dodanych żadnych zadań"
    exam.share_key = f"{hex(exam.scout.user.id * 7312)}{hex(exam.id * 2137)}"

    return exam
