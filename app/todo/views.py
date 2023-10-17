"""
Views for Todo
"""

# from drf_spectacular.utils import ()
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from todo.serializers import TodoSerializer, TaskSerializer
from core.models import Todo, Task

# Create your views here.


class TodoViewSet(viewsets.ModelViewSet):
    """
    Views to manage Todo APIs
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

    def get_queryset(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user).order_by("-id")


class TaskViewSet(
    viewsets.GenericViewSet,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
):
    """
    View for managing Tasks related to Todo
    """

    serializer_class = TaskSerializer
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        """
        Filter queryset to authenticated user
        """
        return self.queryset.filter(todo__user=self.request.user).order_by("id")
