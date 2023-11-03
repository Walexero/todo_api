"""
Views for Todo
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404
from todo.serializers import TodoSerializer, TaskSerializer
from core.models import Todo, Task
from .mixins import BatchUpdateRouteMixin

# Create your views here.


@extend_schema_view(
    create=extend_schema(description="Creates a new Todo"),
    destroy=extend_schema(
        description="Deletes the specified todo, the todo ID is required"
    ),
    partial_update=extend_schema(
        description="Updates specified properties on the Todo, not all fields are required to perform updates"
    ),
    update=extend_schema(
        description="Updates the Todo, all fields are required to perform the update"
    ),
    list=extend_schema(description="Lists all Todos"),
    retrieve=extend_schema(
        description="Retrieves a specified todo based on the todo ID"
    ),
    batch_update=extend_schema(description="Update Specified Todo Ordering"),
)
class TodoViewSet(BatchUpdateRouteMixin, viewsets.ModelViewSet):
    """todo-
    Views to manage Todo APIs. The ordering field signifies the order in which the response is to be ordered in the UI
    """

    serializer_class = TodoSerializer
    queryset = Todo.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Create a new todo
        """
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)

    def get_queryset(self, ids=None):  #
        if self.request.user.is_authenticated:
            if ids:
                return self.queryset.filter(user=self.request.user, id__in=ids)

            return self.queryset.filter(user=self.request.user).order_by("-id")


@extend_schema_view(
    list=extend_schema(
        description="Returns a List of all tasks related to a specific Todo"
    ),
    retrieve=extend_schema(
        description="Returns the details of a specific task. Accepts the task ID as a query value"
    ),
    partial_update=extend_schema(
        description="All fields are not required to be updated. You have the option to update specific properties you choose to update"
    ),
    update=extend_schema(
        description="All fields are required to perform update on the task"
    ),
    destroy=extend_schema(
        description="Deletes the specified task to delete. The task ID is required"
    ),
    create=extend_schema(
        description="Creates a new task related to a todo. The todo ID is required"
    ),
    batch_update=extend_schema(description="Update Specified Task Ordering"),
)
class TaskViewSet(BatchUpdateRouteMixin, viewsets.ModelViewSet):
    """
    View for managing Tasks related to Todo. . The ordering field signifies the order in which the response is to be ordered in the UI
    """

    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def perform_create(self, serializer):
        todo = get_object_or_404(Todo, id=self.request.data.get("todo_id"))
        return serializer.save(todo=todo)

    def get_queryset(self, ids=None):
        """
        Filter queryset to authenticated user
        """
        if self.request.user.is_authenticated:
            if ids:
                return self.queryset.filter(
                    todo__user=self.request.user, id__in=ids
                ).order_by("id")

            return self.queryset.filter(todo__user=self.request.user).order_by("id")
