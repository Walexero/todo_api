"""
Database Models
"""
import json
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from django.conf import settings


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
        return f"{first_name} {last_name}"


class Todo(models.Model):
    """
    Todo Object
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Task(models.Model):
    """
    Task Object
    """

    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name="tasks")
    task = models.CharField(max_length=1000)
    completed = models.BooleanField(default=False)

    def __str__(self):
        # return f'{"id": self.id,"task": self.task}'
        # return json.dumps({"id": self.id, "task": self.task})
        return self.task
