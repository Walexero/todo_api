"""
Database Models
"""
import json
from datetime import datetime
from django.db import models
from django.db.models import Max
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from django.conf import settings
from django.utils import timezone
from datetime import datetime


# Create your models here.
class UserManager(BaseUserManager):
    """
    Manager for users
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a new User without privileges
        """
        if not email:
            raise ValueError("User must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, email, password):
        """
        Create and return a new superuser
        """
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self.db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    User Model
    """

    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Todo(models.Model):
    """
    Todo Object
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(default="", max_length=255, null=True, blank=True)
    last_added = models.DateTimeField(
        default=timezone.now, null=True, blank=True
    )  # auto_now=True
    completed = models.BooleanField(default=False)
    ordering = models.IntegerField(null=True, blank=True)

    @property
    def update_last_added(self):
        self.last_added = timezone.now()

    @property
    def increment_ordering(self):
        user_todos = Todo.objects.filter(user=self.user)
        user_todos_count = user_todos.count()

        if user_todos_count == 0:
            self.ordering = 1
            # self.save()
        elif user_todos_count > 0:
            highest_ordering = user_todos.aggregate(Max("ordering"))
            self.ordering = highest_ordering["ordering__max"] + 1
            # self.save()

    def save(self, *args, **kwargs):
        # if not self.last_added:
        self.update_last_added
        if self.ordering is None:
            self.increment_ordering
        super(Todo, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Task(models.Model):
    """
    Task Object
    """

    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name="tasks")
    task = models.CharField(max_length=1000, null=True, blank=True)
    completed = models.BooleanField(default=False)
    ordering = models.IntegerField(null=True, blank=True)

    @property
    def increment_ordering(self):
        todo_tasks = Task.objects.filter(todo=self.todo)
        todo_tasks_count = todo_tasks.count()
        if todo_tasks_count == 0:
            self.ordering = 1
            # self.save()
        elif todo_tasks_count > 0:
            highest_ordering = todo_tasks.aggregate(Max("ordering"))
            self.ordering = highest_ordering["ordering__max"] + 1
            # self.save()

    def save(self, *args, **kwargs):
        self.increment_ordering
        super(Task, self).save(*args, **kwargs)

    def __str__(self):
        return self.task
