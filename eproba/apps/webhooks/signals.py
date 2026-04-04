from apps.webhooks.tasks import trigger_webhooks
from apps.worksheets.models import Task
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


def serialize_task(task_obj):
    return {
        "id": str(task_obj.id),
        "worksheet_id": str(task_obj.worksheet.id),
        "task": task_obj.task,
        "status": task_obj.status,
    }


@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if instance.id:
        try:
            old_task = Task.objects.get(id=instance.id)
            instance._old_status = old_task.status
            instance._old_approver_id = old_task.approver_id
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    payload = serialize_task(instance)

    old_status = getattr(instance, "_old_status", None)
    old_approver_id = getattr(instance, "_old_approver_id", None)

    status_changed = created or (
        old_status is not None and old_status != instance.status
    )
    approver_changed = (
        old_approver_id is not None and old_approver_id != instance.approver_id
    )

    if status_changed:
        # Notify the user their task status changed
        trigger_webhooks("task.status_changed", instance.worksheet.user, payload)

        # If status changed to 1 (Waiting for approval), notify the approver
        if instance.status == 1 and instance.approver:
            trigger_webhooks("task.sent_to_review", instance.approver, payload)

    elif approver_changed and instance.status == 1 and instance.approver:
        # If task was already awaiting approval but was reassigned to another approver
        trigger_webhooks("task.sent_to_review", instance.approver, payload)
