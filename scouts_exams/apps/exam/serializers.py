from apps.users.models import Scout
from rest_framework import serializers

from .models import Exam, Task


class TaskSerializer(serializers.ModelSerializer):
    approver = serializers.PrimaryKeyRelatedField(
        queryset=Scout.objects.all(), required=False, source="approver.user"
    )

    class Meta:
        model = Task
        fields = ["id", "task", "description", "status", "approver", "approval_date"]

    def update(self, instance, validated_data):
        task = validated_data
        Task.objects.filter(id=instance.id).update(
            task=task["task"] if "task" in task else instance.task,
            description=task["description"]
            if "description" in task
            else instance.description,
            approver=task["approver"]["user"]
            if "approver" in task
            else instance.approver,
            status=task["status"] if "status" in task else instance.status,
            approval_date=task["approval_date"]
            if "approval_date" in task
            else instance.approval_date,
        )
        return Task.objects.get(id=instance.id)


class ExamSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, required=False)
    user = serializers.PrimaryKeyRelatedField(
        queryset=Scout.objects.all(), required=False, source="scout.user"
    )

    supervisor = serializers.PrimaryKeyRelatedField(
        queryset=Scout.objects.all(),
        required=False,
        allow_null=True,
        source="supervisor.user",
    )

    class Meta:
        model = Exam
        fields = ["id", "name", "user", "supervisor", "is_archived", "tasks"]

    def create(self, validated_data):
        tasks = validated_data.pop("tasks") if "tasks" in validated_data else []
        exam = Exam.objects.create(**validated_data)
        for task in tasks:
            Task.objects.create(
                exam=exam,
                approver=task.approver.scout if task.approver is not None else None,
                **task
            )
        return exam
