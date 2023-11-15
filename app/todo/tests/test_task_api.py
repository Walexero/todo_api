from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.db.models import Max
from core.models import Todo, Task
from todo.serializers import TaskSerializer
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.serializers import DateTimeField
from datetime import timedelta

# from core import models

TASK_URL = reverse("todo:task-list")
TASK_BATCH_UPDATE_ORDERING_URL = reverse("todo:task-batch_update_ordering")
TASK_BATCH_UPDATE = reverse("todo:task-batch_update")
TASK_BATCH_CREATE_URL = reverse("todo:task-batch_create")
TASK_BATCH_DELETE_URL = reverse("todo:task-batch_delete")


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

        self.payload = {
            "todo_id": self.todo.id,
            "task": "Test Task",
            "completed": False,
        }

    def test_create_tasks(self):
        """
        Test that the task was created through
        the api call
        """
        res = self.client.post(TASK_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        task = Task.objects.get(todo__id=self.payload["todo_id"])
        self.assertTrue(task.task, self.payload["task"])

    def test_create_task_update_todo_last_added(self):
        """
        Test that the Todo Last Added gets updated every type a task is added
        """
        res = self.client.post(TASK_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        previous_last_added = self.todo.last_added

        payload2 = {
            "todo_id": self.todo.id,
            "task": "Diff Task",
            "completed": False,
        }
        res = self.client.post(TASK_URL, payload2)

        self.todo.refresh_from_db()
        new_last_added = self.todo.last_added

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.assertFalse(previous_last_added == new_last_added)

    def test_create_task_to_validate_ordering_increment(self):
        """
        Test the created task gets auto incremented whenever a new task is added
        """
        payload2 = {"task": "klsfjldsaf", "todo_id": self.todo.id, "completed": True}

        res = self.client.post(TASK_URL, self.payload)
        res2 = self.client.post(TASK_URL, payload2)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        task1 = Task.objects.get(id=res.data["id"])
        task2 = Task.objects.get(id=res2.data["id"])

        tasks_ordering_max = Task.objects.filter(todo=self.todo).aggregate(
            Max("ordering")
        )

        self.assertEqual(res2.data["ordering"], tasks_ordering_max["ordering__max"])

    def test_batch_create_task_success(self):
        """
        Test that a batch create of a task results in task creation
        """
        todo2 = create_todo(self.user)

        payload = {
            "create_list": [
                self.payload,
                {"task": "klsfjldsaf", "todo_id": self.todo.id, "completed": True},
                {
                    "task": "weqfjdlkfjldkfadf",
                    "todo_id": todo2.id,
                    "completed": False,
                    "todo_last_added": DateTimeField().to_representation(
                        timezone.now().replace(second=0, day=3, hour=0, microsecond=0)
                    ),
                },
                {
                    "task": "vifoeinff",
                    "todo_id": todo2.id,
                    "completed": True,
                    "todo_last_added": DateTimeField().to_representation(
                        timezone.now().replace(second=0, day=3, hour=0, microsecond=0)
                    ),
                },
            ]
        }

        res = self.client.post(TASK_BATCH_CREATE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        tasks = Task.objects.filter(todo__user=self.user)
        serializer = TaskSerializer(tasks, many=True)

        self.assertEqual(serializer.data, res.data)

    def test_task_batch_create_task_success_updates_todo_last_added(self):
        """
        Test creating batch tasks also updates the todo last added field
        """
        todo2 = create_todo(self.user)
        # time_value = t
        current_time = DateTimeField().to_representation(timezone.now().replace(day=3))

        payload = {
            "create_list": [
                self.payload,
                {
                    "task": "klsfjldsaf",
                    "todo_id": self.todo.id,
                    "completed": True,
                    "todo_last_added": current_time,
                },
                {
                    "task": "weqfjdlkfjldkfadf",
                    "todo_id": todo2.id,
                    "completed": False,
                    "todo_last_added": timezone.now(),
                },
                {
                    "task": "vifoeinff",
                    "todo_id": todo2.id,
                    "completed": True,
                    "todo_last_added": timezone.now(),
                },
            ]
        }

        res = self.client.post(TASK_BATCH_CREATE_URL, payload, format="json")
        self.todo.refresh_from_db()
        todo_last_added = DateTimeField().to_representation(self.todo.last_added)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(todo_last_added, current_time)

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
        Test updating a specific task
        """
        task = create_task(self.todo, "Test Task")

        payload = {"task": "Updated Test Task", "completed": True}

        url = detail_url(task.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        serializer = TaskSerializer(task)

        self.assertQuerySetEqual(res.data, serializer.data)

    def test_batch_update_task_ordering(self):
        """
        Test updating a batch of tasks ordering
        """
        task1 = create_task(self.todo, "ksdlfjsldf")
        task1.increment_ordering
        task2 = create_task(self.todo, "ksldklsdf")
        task2.increment_ordering
        task3 = create_task(self.todo, "kdfjoviaisd")
        task3.increment_ordering

        payload = {
            "ordering_list": [
                {"id": task1.id, "ordering": task3.ordering},
                {"id": task2.id, "ordering": task1.ordering},
                {"id": task3.id, "ordering": task2.ordering},
            ]
        }
        res = self.client.patch(TASK_BATCH_UPDATE_ORDERING_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tasks = Task.objects.filter(todo=self.todo).order_by("id")
        task1.refresh_from_db()

        serializer = TaskSerializer(tasks, many=True)

        self.assertEqual(task1.ordering, payload["ordering_list"][0]["ordering"])

        self.assertEqual(serializer.data, res.data)

    def test_batch_task_update_succeeds(self):
        """
        Test that the batch update of a task succeeds
        """
        task1 = create_task(self.todo, "ksdlfjsldf")
        # task1.increment_ordering/
        task2 = create_task(self.todo, "ksldklsdf")
        # task2.increment_ordering
        task3 = create_task(self.todo, "kdfjoviaisd")
        # task3.increment_ordering

        payload = {
            "update_list": [
                {
                    "id": task1.id,
                    "task": "kdvsniosdnf",
                    "completed": False,
                    "todo_last_added": timezone.now().replace(day=3, microsecond=0),
                },
                {
                    "id": task2.id,
                    "task": "kdfjsdfjvsf",
                    "completed": True,
                    "todo_last_added": timezone.now().replace(day=3, microsecond=0),
                },
                {
                    "id": task3.id,
                    "task": "kvosdif dsjfksldfsfsdfsfsdf",
                    "todo_last_added": timezone.now().replace(day=3, microsecond=0),
                },
            ]
        }
        res = self.client.patch(TASK_BATCH_UPDATE, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tasks = Task.objects.filter(todo=self.todo).order_by("id")

        serializer = TaskSerializer(tasks, many=True)

        self.assertQuerysetEqual(serializer.data, res.data)

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

    def test_task_batch_delete_with_invalid_id_returns_success(self):
        """
        Test that a batch delete with an invalid id does not result in other delete operations from being carried out
        """
        task1 = create_task(self.todo, "dslkflasjdffda")
        task2 = create_task(self.todo, "ksdfjlsdafsfaf")
        task3 = create_task(self.todo, "kldjvoasfdasf")

        payload = {"delete_list": [task1.id, task2.id, 839283233]}

        res = self.client.delete(TASK_BATCH_DELETE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tasks = Task.objects.filter(todo=self.todo)
        self.assertEqual(tasks.count(), 1)

    def test_task_batch_delete_success(self):
        """
        Test that a batch delete is completed successfully
        """
        task1 = create_task(self.todo, "dslkflasjdffda")
        task2 = create_task(self.todo, "ksdfjlsdafsfaf")
        task3 = create_task(self.todo, "kldjvoasfdasf")

        payload = {"delete_list": [task1.id, task2.id, task3.id]}

        res = self.client.delete(TASK_BATCH_DELETE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(res.data, [])

        tasks = Task.objects.filter(todo=self.todo)
        self.assertEqual(tasks.count(), 0)
