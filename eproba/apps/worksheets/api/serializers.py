from apps.users.api.serializers import PublicUserSerializer
from apps.users.models import User
from apps.worksheets.models import Task, TemplateTask, TemplateWorksheet, Worksheet
from rest_framework import serializers


class ScopeField(serializers.Field):
    def to_representation(self, obj):
        if obj.organization is not None:
            return "organization"
        elif obj.team is not None:
            return "team"
        return None

    def to_internal_value(self, data):
        request = self.parent.context.get("request")
        user = getattr(request, "user", None)
        if data == "team":
            if user and hasattr(user, "patrol"):
                return {"team": user.patrol.team, "organization": None}
            raise serializers.ValidationError("User is not assigned to a patrol.")
        elif data == "organization":
            if user and hasattr(user, "patrol"):
                return {"organization": user.patrol.team.organization, "team": None}
            raise serializers.ValidationError("User is not assigned to a patrol.")
        raise serializers.ValidationError("Invalid scope value.")


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for a Task model with improved maintainability."""

    id = serializers.UUIDField(required=False)
    approver_name = serializers.CharField(
        source="approver.rank_nickname", read_only=True
    )
    worksheet = serializers.PrimaryKeyRelatedField(
        queryset=Worksheet.objects.all(), write_only=True, required=False
    )
    clear_status = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = [
            "id",
            "task",
            "description",
            "status",
            "approver",
            "approver_name",
            "approval_date",
            "worksheet",
            "notes",
            "category",
            "order",
            "clear_status",
        ]

    def to_representation(self, instance):
        """Custom representation to hide notes field based on user permissions."""
        data = super().to_representation(instance)
        request = self.context.get("request")

        # Hide notes field if user doesn't have sufficient permissions
        if request and hasattr(request, "user") and request.user.is_authenticated:
            if request.user.function < 4 and request.user != instance.worksheet.user:
                data.pop("notes", None)
        else:
            data.pop("notes", None)

        return data

    def update(self, instance, validated_data):
        """Update method with clear_status functionality."""
        # Handle clear_status field
        clear_status = validated_data.pop("clear_status", False)
        if clear_status:
            validated_data["status"] = 0
            validated_data["approval_date"] = None
            validated_data["approver"] = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TemplateTaskSerializer(serializers.ModelSerializer):
    """Serializer for TemplateTask model."""

    class Meta:
        model = TemplateTask
        fields = ["id", "task", "description", "template_notes", "category", "order"]


class TemplateWorksheetSummarySerializer(serializers.ModelSerializer):
    """Serializer for template summary without tasks - used for linking templates to worksheets."""

    class Meta:
        model = TemplateWorksheet
        fields = ["id", "name", "description", "image"]


class WorksheetSerializer(serializers.ModelSerializer):
    """
    Serializer for a Worksheet model with nested task management.
    """

    tasks = TaskSerializer(many=True, required=False)
    user = PublicUserSerializer(read_only=True)
    user_id = serializers.UUIDField(
        source="user.id", required=False
    )  # will be write-only in future
    supervisor_name = serializers.CharField(
        source="supervisor.rank_nickname", read_only=True
    )
    is_deleted = serializers.BooleanField(source="deleted", read_only=True)
    template = TemplateWorksheetSummarySerializer(read_only=True)
    template_id = serializers.UUIDField(
        source="template.id", write_only=True, required=False
    )

    class Meta:
        model = Worksheet
        fields = [
            "id",
            "name",
            "description",
            "user",
            "user_id",
            "updated_at",
            "created_at",
            "supervisor",
            "supervisor_name",
            "deleted",
            "is_deleted",
            "is_archived",
            "tasks",
            "notes",
            "template",
            "template_id",
            "final_challenge",
            "final_challenge_description",
        ]

    def to_representation(self, instance):
        """Custom representation for deleted worksheets and permission-based field access."""
        data = super().to_representation(instance)
        request = self.context.get("request")

        if instance.deleted:
            # Hide most of the data for deleted worksheets
            data.update(
                {
                    "tasks": [],
                    "supervisor": None,
                    "name": "Deleted",
                    "user": None,
                    "is_archived": False,
                    "notes": "",
                    "description": "",
                }
            )

        # Hide notes field if user doesn't have sufficient permissions
        if request and hasattr(request, "user") and request.user.is_authenticated:
            if request.user.function < 4 and request.user != instance.user:
                data.pop("notes", None)
        else:
            data.pop("notes", None)

        return data

    def validate_user_id(self, value):
        """Validate that the user exists."""
        if value:
            if not User.objects.filter(id=value).exists():
                raise serializers.ValidationError("User does not exist")
        return value

    def create(self, validated_data):
        # Extract tasks data before creating worksheet
        tasks_data = validated_data.pop("tasks", [])

        # Handle template relationship
        template_data = validated_data.pop("template", None)

        # Create worksheet instance
        worksheet = Worksheet.objects.create(**validated_data)

        # Set template if provided
        if template_data and template_data.get("id"):
            try:
                template = TemplateWorksheet.objects.get(id=template_data["id"])
                worksheet.template = template
                worksheet.save()
            except TemplateWorksheet.DoesNotExist:
                pass

        # Create tasks
        self._create_tasks(worksheet, tasks_data)

        return worksheet

    def _create_tasks(self, worksheet, tasks_data):
        """Create tasks for a worksheet using TaskSerializer."""
        for task_data in tasks_data:
            if task_data.get("task"):  # Only create if task name exists
                task_data["worksheet"] = worksheet.id
                task_serializer = TaskSerializer(data=task_data, context=self.context)
                task_serializer.is_valid(raise_exception=True)
                task_serializer.save()

    def update(self, instance, validated_data):
        # Extract tasks data before updating worksheet
        tasks_data = validated_data.pop("tasks", None)

        # Handle template relationship
        template_data = validated_data.pop("template", None)
        if template_data and template_data.get("id"):
            try:
                template = TemplateWorksheet.objects.get(id=template_data["id"])
                instance.template = template
            except TemplateWorksheet.DoesNotExist:
                pass

        # Update worksheet fields using Django's standard approach
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle tasks update if provided
        if tasks_data is not None:
            self._update_tasks(instance, tasks_data)

        return instance

    def _update_tasks(self, worksheet, tasks_data):
        """
        Update tasks for a worksheet using TaskSerializer.
        """
        # Get current tasks mapped by ID for efficient lookup
        existing_tasks = {str(task.id): task for task in worksheet.tasks.all()}

        # Track which task IDs are being updated/created
        processed_task_ids = set()

        for task_data in tasks_data:
            task_id = task_data.get("id")

            if task_id and str(task_id) in existing_tasks:
                # Update existing task using TaskSerializer
                processed_task_ids.add(str(task_id))
                task_instance = existing_tasks[str(task_id)]
                task_serializer = TaskSerializer(
                    task_instance, data=task_data, context=self.context, partial=True
                )
                task_serializer.is_valid(raise_exception=True)
                task_serializer.save(worksheet=worksheet)
            else:
                # Create new task using TaskSerializer
                task_serializer = TaskSerializer(data=task_data, context=self.context)
                task_serializer.is_valid(raise_exception=True)
                saved_task = task_serializer.save(worksheet=worksheet)
                processed_task_ids.add(str(saved_task.id))

        # Remove tasks that are no longer in the data
        task_ids_to_remove = set(existing_tasks.keys()) - processed_task_ids
        if task_ids_to_remove:
            worksheet.tasks.filter(id__in=task_ids_to_remove).delete()


class TemplateWorksheetSerializer(serializers.ModelSerializer):
    """Serializer for TemplateWorksheet model with nested template tasks."""

    tasks = TemplateTaskSerializer(many=True, required=False)
    scope = ScopeField(source="*")

    class Meta:
        model = TemplateWorksheet
        fields = [
            "id",
            "name",
            "description",
            "template_notes",
            "image",
            "tasks",
            "created_at",
            "updated_at",
            "scope",
        ]

    def create(self, validated_data):
        """Create a template worksheet with nested template tasks."""
        # Extract tasks data before creating template worksheet
        tasks_data = validated_data.pop("tasks", [])

        team = validated_data.pop("team", None)
        organization = validated_data.pop("organization", None)

        if team:
            validated_data["team"] = team
        elif organization is not None:
            validated_data["organization"] = organization

        # Create template worksheet instance
        template_worksheet = TemplateWorksheet.objects.create(**validated_data)

        # Create template tasks
        self._create_template_tasks(template_worksheet, tasks_data)

        return template_worksheet

    def _create_template_tasks(self, template_worksheet, tasks_data):
        """Create template tasks for a template worksheet using TemplateTaskSerializer."""
        for task_data in tasks_data:
            if (
                task_data.get("task")
                or task_data.get("description")
                or task_data.get("template_notes")
            ):
                task_serializer = TemplateTaskSerializer(
                    data=task_data, context=self.context
                )
                task_serializer.is_valid(raise_exception=True)
                task_serializer.save(template=template_worksheet)

    def update(self, instance, validated_data):
        """Update a template worksheet with nested template tasks."""
        # Extract tasks data before updating template worksheet
        tasks_data = validated_data.pop("tasks", None)

        if "team" in validated_data or "organization" in validated_data:
            instance.team = validated_data.pop("team", None)
            instance.organization = validated_data.pop("organization", None)

        # Update template worksheet fields using Django's standard approach
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle template tasks update if provided
        if tasks_data is not None:
            self._update_template_tasks(instance, tasks_data)

        return instance

    def _update_template_tasks(self, template_worksheet, tasks_data):
        """
        Update template tasks for a template worksheet using TemplateTaskSerializer.
        """
        # Get current template tasks mapped by ID for efficient lookup
        existing_tasks = {str(task.id): task for task in template_worksheet.tasks.all()}

        # Track which task IDs are being updated/created
        processed_task_ids = set()

        for task_data in tasks_data:
            task_id = task_data.get("id")

            if task_id and str(task_id) in existing_tasks:
                # Update existing template task using TemplateTaskSerializer
                processed_task_ids.add(str(task_id))
                task_instance = existing_tasks[str(task_id)]
                task_serializer = TemplateTaskSerializer(
                    task_instance, data=task_data, context=self.context, partial=True
                )
                task_serializer.is_valid(raise_exception=True)
                task_serializer.save(template=template_worksheet)
            else:
                # Create new template task using TemplateTaskSerializer
                task_serializer = TemplateTaskSerializer(
                    data=task_data, context=self.context
                )
                task_serializer.is_valid(raise_exception=True)
                saved_task = task_serializer.save(template=template_worksheet)
                processed_task_ids.add(str(saved_task.id))

        # Remove template tasks that are no longer in the data
        task_ids_to_remove = set(existing_tasks.keys()) - processed_task_ids
        if task_ids_to_remove:
            template_worksheet.tasks.filter(id__in=task_ids_to_remove).delete()

    def validate(self, attrs):
        """Custom validation for TemplateWorksheet."""
        return super().validate(attrs)
