"""
Serializers for Todo API
"""

from rest_framework import serializers
from core.models import Todo, Task
from .mixins import (
    BatchUpdateOrderingSerializerMixin,
    BatchUpdateAllSerializerMixin,
    BatchDeleteSerializerMixin,
    BatchCreateSerializerMixin,
)
from django.db import IntegrityError
from django.db.models import Max
from collections import defaultdict
from django.utils import timezone


class BatchOrderingUpdateSerializer(
    BatchUpdateOrderingSerializerMixin, serializers.ListSerializer
):
    """
    Serializer for Todo for updating batch or multiple Todo Ordering
    """

    def update(self, instance, validated_data):
        """
        Update Model Orderings
        """
        model_mapping = {model.id: model for model in instance}

        ordering_mapping = {item["ordering"]: item for item in validated_data}

        updated_values = []

        for ordering, model in ordering_mapping.items():
            model = model_mapping.get(model["id"], None)
            if model:
                model.ordering = ordering
                model.save()
                updated_values.append(model)
        return updated_values

    class Meta:
        fields = ["id", "ordering"]
        read_only_fields = ["id"]


class BatchUpdateAllSerializer(
    BatchUpdateAllSerializerMixin, serializers.ListSerializer
):
    """
    Serializer for Todo for updating batch or multiple Todo Ordering
    """

    # TODO: modify to implement updatee all logic
    def update(self, instance, validated_data):
        """
        Update Model Orderings
        """
        model_mapping = {model.id: model for model in instance}

        update_mapping = {item["ordering"]: item for item in validated_data}

        updated_values = []

        for ordering, model in ordering_mapping.items():
            model = model_mapping.get(model["id"], None)
            if model:
                model.ordering = ordering
                model.save()
                updated_values.append(model)
        return updated_values

    class Meta:
        fields = ["id", "ordering"]
        read_only_fields = ["id"]


# class CustomDateTimeFieldSerializer(serializers.DateTimeField):
# def to_representation(self, value):
# value = timezone.localtime(value)
# return value.strftime("%Y-%m-%dT%H:%M:%S")
#
# def to_internal_value(self, value):
# parsed_datetime = timezone.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
# return timezone.make_aware(parsed_datetime)


class BatchCreateSerializer(BatchCreateSerializerMixin, serializers.ListSerializer):
    """
    Serializer for performing batch create
    """

    # last_added = CustomDateTimeFieldSerializer()

    def increment_obj_ordering_todo(self, obj):
        user = self.context["request"].user
        for i, object in enumerate(obj):
            user_todos = Todo.objects.filter(user=user)
            user_todos_count = user_todos.count()
            object.ordering = user_todos_count + (i + 1)

    def increment_obj_ordering_task(self, obj):
        obj_count = defaultdict(int)

        for object in obj:
            todo_tasks = Task.objects.filter(todo__id=object.todo_id)
            obj_count[object.todo_id] += 1
            todo_tasks_count = todo_tasks.count()
            object.ordering = todo_tasks_count + obj_count[object.todo_id]

    def assign_bulk_tasks_todo_id(self, tasks, todo_list):
        bulk_task = []
        for i, task in enumerate(tasks):
            if len(task) > 1:
                for task_obj in task:
                    task_obj["todo_id"] = todo_list[i].id
                    bulk_task.append(task_obj)
            else:
                task[0]["todo_id"] = todo_list[i].id
                bulk_task.append(task[0])

        task_result = [Task(**attrs) for attrs in bulk_task]
        self.increment_obj_ordering_task(task_result)

        try:
            Task.objects.bulk_create(task_result)

            # self.increment_obj_ordering(task_result)
        except IntegrityError as e:
            raise ValidationError(e)

    def create(self, validated_data):
        print("the validated data", validated_data)
        tasks = [task_field.pop("tasks", None) for task_field in validated_data]

        todo_result = [self.child.Meta.model(**attrs) for attrs in validated_data]
        self.increment_obj_ordering_todo(todo_result)

        try:
            self.child.Meta.model.objects.bulk_create(todo_result)
            # self.increment_obj_ordering(todo_result)
        except IntegrityError as e:
            raise ValidationError(e)

        self.assign_bulk_tasks_todo_id(tasks, todo_result)

        return todo_result

    class Meta:
        fields = ["id", "title", "tasks", "last_added", "completed", "ordering"]
        read_only_fields = ["id", "ordering"]


class BatchDeleteSerializer(BatchDeleteSerializerMixin, serializers.ListSerializer):
    """
    Serializer for performing batch delete
    """

    def delete(self, instance, validated_data):
        pass

    class Meta:
        pass


class SerializerGetListSerializerClassInitMixin:
    """
    Mixin to allow setting the list_serializer_class for a serializer
    """

    list_serializer_type_classes = {
        "batch_update_all": BatchUpdateAllSerializer,
        "batch_update_ordering": BatchOrderingUpdateSerializer,
        "batch_delete": BatchDeleteSerializer,
        "batch_create": BatchCreateSerializer,
    }

    def __init__(self, *args, **kwargs):
        list_serializer_type = kwargs.pop("type", None)
        user = kwargs.pop("user", None)

        if list_serializer_type == "batch_create":
            self.Meta.read_only_fields = ["id", "ordering"]
        else:
            self.Meta.read_only_fields = ["id", "last_added", "ordering"]

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # set the list serializer based on the list_serializer_type
        if list_serializer_type is not None:
            self.Meta.list_serializer_class = self.list_serializer_type_classes[
                list_serializer_type
            ]


class TaskSerializer(
    SerializerGetListSerializerClassInitMixin, serializers.ModelSerializer
):
    """
    Serializer for Tasks
    """

    # todo_title = serializers.CharField(source="todo.title")
    todo_id = serializers.IntegerField(source="todo.id")
    todo_last_added = serializers.DateTimeField(
        source="todo.last_added", required=False
    )

    class Meta:
        list_serializer_class = BatchOrderingUpdateSerializer
        model = Task
        fields = [
            "id",
            "task",
            "completed",
            "todo_id",
            "todo_last_added",
            "ordering",
        ]  #
        read_only = ["todo_last_added", "ordering"]

    #
    def create(self, validated_data):
        """
        Creates a new task
        """
        todo = validated_data.pop("todo", None)
        # update the todo last_added using its property
        # todo.update_last_added

        if todo is not None:
            task = Task.objects.create(
                todo=todo,
                task=validated_data["task"],
                completed=validated_data["completed"],
            )
            # task.increment_ordering
            todo.save()
            return task


class TaskTodoSerializer(serializers.ModelSerializer):
    """
    Serializer to be used by the Todo when
    for serializing a task
    """

    class Meta:
        model = Task
        fields = ["id", "task", "completed", "ordering"]
        read_only_fields = ["ordering"]


class TodoSerializer(
    SerializerGetListSerializerClassInitMixin, serializers.ModelSerializer
):
    """
    Serializer for Todos
    """

    tasks = TaskTodoSerializer(
        many=True, required=False
    )  # serializers.StringRelatedField(many=True)

    def _get_or_create_tasks(self, tasks, todo):
        """
        Handle getting or creating a tasks as needed
        """
        for task in tasks:
            task_obj, created = Task.objects.get_or_create(todo=todo, **task)
            # task_obj.increment_ordering
            todo.tasks.add(task_obj)

    def create(self, validated_data):
        """
        Create a Todo
        """
        tasks = validated_data.pop("tasks", [])
        todo = Todo.objects.create(**validated_data)
        # todo.increment_ordering
        self._get_or_create_tasks(tasks, todo)
        return todo

    def update(self, instance, validated_data):
        """
        Update a Todo
        """
        tasks = validated_data.pop("tasks", None)
        if tasks is not None:
            for task in instance.tasks.all():
                task.delete()

            self._get_or_create_tasks(tasks, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    class Meta:
        list_serializer_class = BatchOrderingUpdateSerializer
        model = Todo
        fields = ["id", "title", "tasks", "last_added", "completed", "ordering"]
        read_only_fields = ["id", "last_added", "ordering"]
