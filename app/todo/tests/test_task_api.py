from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Todo, Task
from todo.serializers import TaskSerializer
from django.contrib.auth import get_user_model
import json
from django.urls import reverse

# from core import models


TASK_URL = reverse("todo:task-list")


def detail_url(task_id):
    """
    Create and return url to retrieve a task detail
    """
    return reverse("todo:task-detail", args=[task_id])


def create_user(email="user@example.com", password="Awesomeuser123"):
    """
    Create and return a user
    """
    return get_user_model().objects.create_user(
        email=email, password=password, first_name="Test", last_name="User"
    )


def create_todo(user):
    """
    Create and return a todo
    """
    return Todo.objects.create(title="Test Todo", user=user)


def create_task(todo, task_text):
    """
    Create and return a task
    """
    return Task.objects.create(todo=todo, task=task_text)


class PublicTaskApiTests(TestCase):
    """
    Test unauthenticated API requests
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test auth is required for retrieving tasks
        """
        res = self.client.get(TASK_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTaskApiTest(TestCase):
    """
    Test the task api for authenticated users
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.todo = create_todo(self.user)

    def test_get_tasks(self):
        """
        Tests that the task was retrieved for authenticated users
        """
        task1 = create_task(self.todo, "Test Task 1")
        task2 = create_task(self.todo, "Test Task 2")

        res = self.client.get(TASK_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data[0]["id"], task1.id)
        self.assertEqual(res.data[1]["id"], task2.id)

    def test_retrieved_tasks_limited_to_user(self):
        """
        Test that the retreived tags are limited only to the user
        """
        other_user = create_user("other@example.com")
        other_todo = create_todo(other_user)

        create_task(other_todo, "Other Todo Task 1")
        create_task(other_todo, "Other todo task 2")
        task = create_task(self.todo, "Test Task 1")

        res = self.client.get(TASK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        serializer = TaskSerializer(task)
        self.assertEqual(res.data, [serializer.data])

    def test_other_user_cannot_retrieve_another_user_tasks(self):
        """
        Test that other users are not able to get access to tasks related to another user
        """
        other_user = create_user("other@example.com")

        other_todo = create_todo(other_user)
        task = create_task(self.todo, "Test Task")
        create_task(other_todo, "Other task 1")
        create_task(other_todo, "Other task 2")
        self.client.logout()
        self.client.force_authenticate(other_user)

        url = detail_url(task.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_task(self):
        """
        Test updating a specific tag
        """
        task = create_task(self.todo, "Test Task")

        payload = {"task": "Updated Test Task", "completed": True}

        url = detail_url(task.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        serializer = TaskSerializer(task)

        self.assertQuerySetEqual(res.data, serializer.data)

    def test_delete_task_without_other_task(self):
        """
        Test deleting a task when no other users task exist
        """
        task = create_task(self.todo, "Test task")

        url = detail_url(task.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tasks = Task.objects.filter(todo=self.todo)
        self.assertFalse(tasks.exists())

    def test_delete_task_when_other_user_task_exist(self):
        """
        Tests that the correct tag is deleted for the authenticated user and no other tags was deleted
        """
        other_user = create_user("other@example.com")
        other_todo = create_todo(other_user)
        create_task(other_todo, "Other user task")
        create_task(other_todo, "Another other user task")

        task = create_task(self.todo, "Test task")

        url = detail_url(task.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tasks = Task.objects.filter(todo__user=self.user)
        self.assertFalse(tasks.exists())

    def test_delete_other_user_task_by_another_user(self):
        """
        Test that a user should not be able to delete tasks belonging to another User todo
        """
        other_user = create_user("other@example.com")
        other_todo = create_todo(other_user)
        other_task = create_task(other_todo, "Other user task")
        create_task(other_todo, "Another other user task")

        url = detail_url(other_task.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
