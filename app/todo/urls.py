"""
URLS for Todo API
"""

from django.urls import re_path, include
from rest_framework.routers import DefaultRouter

from todo import views

router = DefaultRouter()
router.register("todos", views.TodoViewSet)
router.register("tasks", views.TaskViewSet)

app_name = "todo"

urlpatterns = [re_path("", include(router.urls))]
