from apps.users.models import Scout
from rest_framework import serializers

from .models import Exam, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "task", "description", "status", "approver", "approval_date"]


class ExamSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, required=False)

    class Meta:
        model = Exam
        fields = ["id", "name", "user", "supervisor", "is_archived", "tasks"]

    user = serializers.PrimaryKeyRelatedField(
        queryset=Scout.objects.all(), required=False, source="scout.user"
    )

    def create(self, validated_data):
        tasks = validated_data.pop("tasks") if "tasks" in validated_data else []
        exam = Exam.objects.create(**validated_data)
        for task in tasks:
            Task.objects.create(exam=exam, **task)
        return exam
