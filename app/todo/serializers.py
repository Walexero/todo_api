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

    class Meta:
        model = Task
        fields = ["id", "task"]  # , "todo_title"


class TodoSerializer(serializers.ModelSerializer):
    """
    Serializer for Todos
    """

    tasks = TaskSerializer(
        many=True, required=False
    )  # serializers.StringRelatedField(many=True)

    class Meta:
        model = Todo
        fields = ["id", "title", "tasks"]
        read_only_fields = ["id"]
