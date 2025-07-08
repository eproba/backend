def prepare_worksheet(worksheet):
    _all = 0
    _done = 0
    worksheet.show_submit_task_button = False
    worksheet.show_sent_tasks_button = False
    worksheet.show_description_column = False
    for task in worksheet.tasks.all():
        _all += 1
        if task.status == 2:
            _done += 1
        elif task.status in [0, 3]:
            worksheet.show_submit_task_button = True
        elif task.status == 1:
            worksheet.show_sent_tasks_button = True
        if task.description != "":
            worksheet.show_description_column = True
    if _all != 0:
        percent = int(round(_done / _all, 2) * 100)
        worksheet.percent = f"{percent}%"
    else:
        worksheet.percent = "Nie masz jeszcze dodanych żadnych zadań"

    return worksheet
