from core import models
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from todo.serializers import TodoSerializer


TODO_URL = reverse("todo:todo-list")


def detail_url(todo_id):
    """
    Returns the url for a todo detail
    """
    return reverse("todo:todo-detail", args=[todo_id])


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
    return models.Todo.objects.create(title="Test Todo", user=user)


def create_task(todo, task_text):
    """
    Create and return a task
    """
    return models.Task.objects.create(todo=todo, task=task_text)


class PublicTodoApiTests(TestCase):
    """
    Test unauthenticated requests to the Todo Api
    """

    def setUp(self):
        self.client = APIClient()

    def test_create_unauthenticated_todo(self):
        """
        Test unauthenticated users cannot create todo
        """

        res = self.client.get(TODO_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTodoApiTest(TestCase):
    """
    Test authenticated todo api requests
    """

    def setUp(self):
        self.client = APIClient()

    def test_create_todo_for_unauthenticated_user(self):
        """
        Test creating a todo for an unauthenticated user returns a 401
        """
        payload = {"title": "Test todo"}

        res = self.client.post(TODO_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_todo_for_authenticated_user(self):
        """
        Test creating a todo for an authenticated user
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)

        payload = {"title": "Test todo"}

        res = self.client.post(TODO_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        todo = models.Todo.objects.get(id=res.data["id"])

        self.assertEqual(todo.title, payload["title"])

    def test_retrieve_todos_for_unauthenticated_user(self):
        """
        Test retreiving todos for unauthenticated user
        """
        other_user = create_user()
        create_todo(other_user)
        create_todo(other_user)

        res = self.client.get(TODO_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_todos_for_authenticated_user(self):
        """
        Test retrieving todos for authenticated user
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)

        create_todo(self.user)
        create_todo(self.user)

        res = self.client.get(TODO_URL)

        todos = models.Todo.objects.filter(user=self.user).order_by("-id")

        serializer = TodoSerializer(todos, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertQuerySetEqual(res.data, serializer.data)

    def test_retrieving_todos_meant_only_for_authenticated_user(self):
        """
        Test retrieving the todo meant only for the authenticated user making the request and to make sure no todos for other users are returned
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)

        other_user = create_user("other@example.com")
        create_todo(self.user)
        create_todo(self.user)
        create_todo(other_user)

        res = self.client.get(TODO_URL)

        todos = models.Todo.objects.filter(user=self.user).order_by("-id")

        serializer = TodoSerializer(todos, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(todos.count(), len(serializer.data))
        self.assertQuerySetEqual(res.data, serializer.data)

    def test_retrieve_todo(self):
        """
        Test retrieving a todo
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)

        todo = create_todo(self.user)

        url = detail_url(todo.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer = TodoSerializer(todo)

        self.assertEqual(res.data, serializer.data)

    def test_todo_list_limited_to_user(self):
        """
        Test todo returned is only for authenticated user
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)

        other_user = create_user(email="user2@example.com")

        create_todo(other_user)
        create_todo(other_user)
        create_todo(self.user)

        res = self.client.get(TODO_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        todo = models.Todo.objects.filter(user=self.user)

        self.assertEqual(todo.count(), 1)

        serializer = TodoSerializer(todo, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_get_todo_with_task_serializer(self):
        """
        Test the todo with tasks added to verify the tasks associated to the todo is returned
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        todo = create_todo(self.user)
        create_task(todo, "Test task 1")
        create_task(todo, "Task test 2")
        todo.refresh_from_db()
        serializer = TodoSerializer(todo)

        url = detail_url(todo.id)

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertQuerySetEqual(res.data, serializer.data)

    def test_delete_todo_limited_to_user(self):
        """
        Test deleting a users todo items
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        todo = create_todo(self.user)
        create_todo(self.user)
        # todo.refresh_from_db()
        url = detail_url(todo.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        user_todos = models.Todo.objects.filter(user=self.user)
        self.assertEqual(user_todos.count(), 1)

    # todo: test partial update
    def test_partial_update_of_todo(self):
        """
        Test a put request on a todo object
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        todo = create_todo(self.user)
        create_task(todo, "Test task 1")
        create_task(todo, "Task test 2")
        url = detail_url(todo.id)

        payload = {"title": "Made a partial update to the todo"}

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], payload["title"])

    def test_partial_update_of_user_todo_by_another_user(self):
        """
        Test making a partial update of a User's todo by another user returns a bad request
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        user_todo = create_todo(self.user)
        create_todo(self.user)
        self.client.logout()
        other_user = create_user("other@example.com")
        create_todo(other_user)
        self.client.force_authenticate(other_user)
        url = detail_url(user_todo.id)
        payload = {"title": "Updating todo title by another user"}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_update_of_todo(self):
        """
        Test making a full update on the todo by the user
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        todo = create_todo(self.user)
        create_task(todo, "Test task 1")
        create_task(todo, "Task test 2")
        url = detail_url(todo.id)

        payload = {"title": "Made a partial update to the todo"}

        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], payload["title"])

    def test_updating_todo_user(self):
        """
        Test updating todo user from currently authenticated user fails
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        user_todo = create_todo(self.user)
        create_todo(self.user)
        other_user = create_user("other@example.com")

        url = detail_url(user_todo.id)
        payload = {"user": other_user.id}
        self.client.patch(url, payload)
        self.assertEqual(user_todo.user, self.user)

    def test_updating_tasks_from_todo(self):
        """
        Test that the tasks added to the todo are cleared when the todo tasks are updated
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)
        user_todo = create_todo(self.user)
        task = create_task(user_todo, "new task")

        url = detail_url(user_todo.id)
        payload = {"tasks": [{"task": "dsfasdfdf"}, {"task": "diff task"}]}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        user_todo.refresh_from_db()
        serializer = TodoSerializer(user_todo)
        self.assertEqual(res.data, serializer.data)

    def test_updating_tasks_from_todo_does_not_affect_other_unrelated_tasks(self):
        """
        Test that updating tasks from the todo does not affect other tasks in other todos
        """
        self.user = create_user()
        self.client.force_authenticate(self.user)

        user_todo = create_todo(self.user)
        diff_todo1 = create_todo(self.user)
        diff_todo2 = create_todo(self.user)
        task = create_task(user_todo, "new task")
        create_task(diff_todo1, "diff task")
        create_task(diff_todo2, "sdfasdfadsf")

        url = detail_url(user_todo.id)
        payload = {"tasks": [{"task": "dsfasdfdf"}, {"task": "diff task"}]}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        user_todo.refresh_from_db()
        serializer = TodoSerializer(user_todo)
        self.assertEqual(res.data, serializer.data)

        self.assertEqual(diff_todo1.tasks.count(), 1)
        self.assertEqual(diff_todo2.tasks.count(), 1)
