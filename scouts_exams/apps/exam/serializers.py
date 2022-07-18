from apps.users.models import Scout
from rest_framework import serializers

from .models import Exam, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "task", "description", "status", "approver", "approval_date"]


class ExamSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True)

    class Meta:
        model = Exam
        fields = ["id", "name", "scout", "supervisor", "is_archived", "tasks"]

    scout = serializers.PrimaryKeyRelatedField(
        queryset=Scout.objects.all(), required=False
    )

    def create(self, validated_data):
        tasks = validated_data.pop("tasks")
        exam = Exam.objects.create(**validated_data)
        for task in tasks:
            Task.objects.create(exam=exam, **task)
        return exam
