"""
Views for Todo
"""

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    OpenApiResponse,
)
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from todo.serializers import TodoSerializer, TaskSerializer
from core.models import Todo, Task
from .mixins import (
    BatchRouteMixin,
    BatchUpdateOrderingRouteMixin,
    BatchUpdateRouteMixin,
    BatchCreateRouteMixin,
    BatchDeleteRouteMixin,
)
from .serializers import TodoSerializer, TaskSerializer


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
    batch_create=extend_schema(
        description="Create a batch of Todos",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "create_list": [
                        {"title": "string", "completed": True, "tasks": []},
                        {
                            "title": "string",
                            "completed": True,
                            "tasks": [{"task": "string", "completed": True}],
                        },
                    ]
                },
            ),
            OpenApiExample(
                "Response Body",
                value=[
                    {
                        "id": 0,
                        "title": "string",
                        "tasks": [],
                        "last_added": timezone.now(),
                        "completed": True,
                        "ordering": 1,
                    },
                    {
                        "id": 1,
                        "title": "string",
                        "tasks": [
                            {
                                "id": 0,
                                "task": "string",
                                "completed": True,
                                "ordering": 1,
                            }
                        ],
                        "last_added": timezone.now(),
                        "completed": True,
                        "ordering": 2,
                    },
                ],
            ),
        ],
    ),
    batch_update=extend_schema(
        description="Update Specified Todo Ordering. Only Properties relating To The Todo can be updated using this endpoint. To update a Task Linked to a todo to be batch created. Please use the task endpoint or if the batch_update for updating tasks",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "update_list": [
                        {"title": "string", "completed": True, "id": 0},
                        {"title": "string", "completed": False, "id": 1},
                    ],
                },
            ),
            OpenApiExample(
                "Response Body",
                value=[
                    {
                        "id": 0,
                        "title": "string",
                        "tasks": [],
                        "last_added": timezone.now(),
                        "completed": True,
                        "ordering": 1,
                    },
                    {
                        "id": 1,
                        "title": "string",
                        "tasks": [
                            {
                                "id": 0,
                                "task": "string",
                                "completed": True,
                                "ordering": 1,
                            }
                        ],
                        "last_added": timezone.now(),
                        "completed": True,
                        "ordering": 2,
                    },
                ],
            ),
        ],
    ),
    batch_update_ordering=extend_schema(
        description="Update the ordering of a task",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "ordering_list": [
                        {"id": 0, "ordering": 5},
                        {"id": 1, "ordering": 3},
                    ]
                },
            ),
            OpenApiExample(
                "Response Body",
                value=[
                    {
                        "id": 0,
                        "title": "string",
                        "tasks": [],
                        "last_added": timezone.now(),
                        "completed": True,
                        "ordering": 5,
                    },
                    {
                        "id": 1,
                        "title": "string",
                        "tasks": [
                            {
                                "id": 0,
                                "task": "string",
                                "completed": True,
                                "ordering": 1,
                            }
                        ],
                        "last_added": timezone.now(),
                        "completed": True,
                        "ordering": 3,
                    },
                ],
            ),
        ],
    ),
    batch_delete=extend_schema(
        description="""
        Delete a list of items. The request body is in the following format:
        {
            "delete_list": [1,2,3]
        }
        It takes the ids of the resource to delete as a list.The batch_delete endpoint can not be queried from this UI, you would have to make a raw request.
        ,
        """,
        responses={
            204: OpenApiResponse(description="No response body"),
        },
    ),
)
class TodoViewSet(
    BatchRouteMixin,
    BatchCreateRouteMixin,
    BatchUpdateRouteMixin,
    BatchUpdateOrderingRouteMixin,
    BatchDeleteRouteMixin,
    viewsets.ModelViewSet,
):
    """
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

    def perform_destory(self, serializer):
        """
        Delete a todo
        """
        serializer.destroy()

    def view_name(self):
        return "todo"


@extend_schema_view(
    list=extend_schema(
        description="Returns a List of all tasks related to a specific Todo",
        examples=[
            OpenApiExample(
                "Response Body",
                value={
                    "id": 0,
                    "task": "string",
                    "completed": True,
                    "todo_id": 0,
                    "todo_last_added": timezone.now(),
                    "ordering": 1,
                },
            )
        ],
    ),
    retrieve=extend_schema(
        description="Returns the details of a specific task. Accepts the task ID as a query value",
        examples=[
            OpenApiExample(
                "Response Body",
                value={
                    "id": 0,
                    "task": "string",
                    "completed": True,
                    "todo_id": 0,
                    "todo_last_added": timezone.now(),
                    "ordering": 1,
                },
            )
        ],
    ),
    partial_update=extend_schema(
        description="All fields are not required to be updated. You have the option to update specific properties you choose to update",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "task": "string",
                    "completed": True,
                    "ordering": 1,
                },
            ),
            OpenApiExample(
                "Response Body",
                value={
                    "id": 0,
                    "task": "string",
                    "completed": True,
                    "todo_id": 0,
                    "todo_last_added": timezone.now(),
                    "ordering": 1,
                },
            ),
        ],
    ),
    destroy=extend_schema(
        description="Deletes the specified task to delete. The task ID is required"
    ),
    create=extend_schema(
        description="Creates a new task related to a todo. The todo ID is required",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "task": "string",
                    "completed": True,
                    "todo_id": 0,
                    "todo_last_added": timezone.now(),
                },
            ),
            OpenApiExample(
                "Response Body",
                value={
                    "id": 0,
                    "task": "string",
                    "completed": True,
                    "todo_id": 0,
                    "todo_last_added": timezone.now(),
                    "ordering": 1,
                },
            ),
        ],
    ),
    batch_create=extend_schema(
        description="",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "create_list": [
                        {
                            "task": "string",
                            "completed": True,
                            "todo_id": 0,
                            "todo_last_added": timezone.now(),
                        },
                        {
                            "task": "string",
                            "completed": False,
                            "todo_id": 1,
                            "todo_last_added": timezone.now(),
                        },
                    ]
                },
            ),
            OpenApiExample(
                "Response Body",
                value=[
                    {
                        "id": 0,
                        "task": "string",
                        "completed": True,
                        "todo_id": 0,
                        "todo_last_added": timezone.now(),
                        "ordering": 1,
                    },
                    {
                        "id": 1,
                        "task": "string",
                        "completed": True,
                        "todo_id": 2,
                        "todo_last_added": timezone.now(),
                        "ordering": 1,
                    },
                ],
            ),
        ],
    ),
    batch_update=extend_schema(
        description="Update Specified Task Ordering",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "update_list": [
                        {
                            "id": 0,
                            "task": "string",
                            "completed": True,
                            "todo_last_added": timezone.now(),
                        },
                        {
                            "id": 1,
                            "task": "string",
                            "todo_last_added": timezone.now(),
                        },
                    ]
                },
            ),
            OpenApiExample(
                "Response Body",
                value=[
                    {
                        "id": 0,
                        "task": "string",
                        "completed": True,
                        "todo_id": 0,
                        "todo_last_added": timezone.now(),
                        "ordering": 1,
                    },
                    {
                        "id": 1,
                        "task": "string",
                        "completed": True,
                        "todo_id": 2,
                        "todo_last_added": timezone.now(),
                        "ordering": 1,
                    },
                ],
            ),
        ],
    ),
    batch_update_ordering=extend_schema(
        description="Update the ordering of a task",
        examples=[
            OpenApiExample(
                "Request Body",
                value={
                    "ordering_list": [
                        {"id": 0, "ordering": 5},
                        {"id": 1, "ordering": 3},
                    ]
                },
            ),
            OpenApiExample(
                "Response Body",
                value=[
                    {
                        "id": 0,
                        "task": "string",
                        "completed": True,
                        "todo_id": 0,
                        "todo_last_added": timezone.now(),
                        "ordering": 1,
                    },
                    {
                        "id": 1,
                        "task": "string",
                        "completed": True,
                        "todo_id": 2,
                        "todo_last_added": timezone.now(),
                        "ordering": 1,
                    },
                ],
            ),
        ],
    ),
    batch_delete=extend_schema(
        description="""
        Delete a list of items. The request body is in the following format:
        {
            "delete_list": [1,2,3]
        }
        It takes the ids of the resource to delete as a list. The batch_delete endpoint can not be queried from this UI, you would have to make a raw request.
        ,
        """
    ),
)
class TaskViewSet(
    BatchRouteMixin,
    BatchCreateRouteMixin,
    BatchUpdateRouteMixin,
    BatchUpdateOrderingRouteMixin,
    BatchDeleteRouteMixin,
    viewsets.ModelViewSet,
):
    """
    View for managing Tasks related to Todo. . The ordering field signifies the order in which the response is to be ordered in the UI
    """

    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    http_method_names = ["get", "post", "patch", "delete"]

    def perform_create(self, serializer):
        action_type = self.action

        if action_type == "batch_create":
            return serializer.save()

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

    def view_name(self):
        return "task"
