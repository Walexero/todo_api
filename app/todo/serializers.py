"""
Serializers for Todo API
"""

from rest_framework import serializers
from core.models import Todo, Task
from .mixins import BatchUpdateSerializerMixin


class BatchOrderingUpdateSerializer(
    BatchUpdateSerializerMixin, serializers.ListSerializer
):
    """
    Serializer for Todo for updating batch or multiple Todo Ordering
    """

    def update(self, instance, validated_data):
        """
        Update Model Orderings
        """
        model_mapping = {model.id: model for model in instance}

        ordering_mapping = {item["ordering"]: item for item in validated_data}

        updated_values = []

        for ordering, model in ordering_mapping.items():
            model = model_mapping.get(model["id"], None)
            if model:
                model.ordering = ordering
                model.save()
                updated_values.append(model)
        return updated_values

    class Meta:
        fields = ["id", "ordering"]
        read_only_fields = ["id"]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Tasks
    """

    # todo_title = serializers.CharField(source="todo.title")
    todo_id = serializers.IntegerField(source="todo.id")
    todo_last_added = serializers.DateTimeField(
        source="todo.last_added", required=False
    )

    class Meta:
        list_serializer_class = BatchOrderingUpdateSerializer
        model = Task
        fields = [
            "id",
            "task",
            "completed",
            "todo_id",
            "todo_last_added",
            "ordering",
        ]  #
        read_only = ["todo_last_added", "ordering"]

    def create(self, validated_data):
        """
        Creates a new task
        """
        todo = validated_data.pop("todo", None)
        # update the todo last_added using its property
        todo.update_last_added

        if todo is not None:
            task = Task.objects.create(
                todo=todo,
                task=validated_data["task"],
                completed=validated_data["completed"],
            )
            task.increment_ordering
            todo.save()
            return task


class TaskTodoSerializer(serializers.ModelSerializer):
    """
    Serializer to be used by the Todo when
    for serializing a task
    """

    class Meta:
        model = Task
        fields = ["id", "task", "completed", "ordering"]
        read_only_fields = ["ordering"]


class TodoSerializer(serializers.ModelSerializer):
    """
    Serializer for Todos
    """

    tasks = TaskTodoSerializer(
        many=True, required=False
    )  # serializers.StringRelatedField(many=True)

    def _get_or_create_tasks(self, tasks, todo):
        """
        Handle getting or creating a tasks as needed
        """
        for task in tasks:
            task_obj, created = Task.objects.get_or_create(todo=todo, **task)
            task_obj.increment_ordering
            todo.tasks.add(task_obj)

    def create(self, validated_data):
        """
        Create a Todo
        """
        tasks = validated_data.pop("tasks", [])
        todo = Todo.objects.create(**validated_data)
        todo.increment_ordering
        self._get_or_create_tasks(tasks, todo)
        return todo

    def update(self, instance, validated_data):
        """
        Update a Todo
        """
        tasks = validated_data.pop("tasks", None)
        if tasks is not None:
            for task in instance.tasks.all():
                task.delete()

            self._get_or_create_tasks(tasks, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    class Meta:
        list_serializer_class = BatchOrderingUpdateSerializer
        model = Todo
        fields = ["id", "title", "tasks", "last_added", "completed", "ordering"]
        read_only_fields = ["id", "last_added", "ordering"]
