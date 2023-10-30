"""
Serializers for Todo API
"""

from rest_framework import serializers
from core.models import Todo, Task


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
        model = Task
        fields = ["id", "task", "completed", "todo_id", "todo_last_added"]  #
        read_only = ["todo_last_added"]

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
            todo.save()
            return task


class TaskTodoSerializer(serializers.ModelSerializer):
    """
    Serializer to be used by the Todo when
    for serializing a task
    """

    class Meta:
        model = Task
        fields = ["id", "task", "completed"]


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
            todo.tasks.add(task_obj)

    def create(self, validated_data):
        """
        Create a Todo
        """
        tasks = validated_data.pop("tasks", [])
        todo = Todo.objects.create(**validated_data)
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
        model = Todo
        fields = ["id", "title", "tasks", "last_added", "completed"]
        read_only_fields = ["id", "last_added"]
