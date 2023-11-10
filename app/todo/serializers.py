"""
Serializers for Todo API
"""

from rest_framework import serializers
from core.models import Todo, Task
from .mixins import (
    BatchUpdateOrderingSerializerMixin,
    BatchUpdateSerializerMixin,
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


class BatchUpdateSerializer(BatchUpdateSerializerMixin, serializers.ListSerializer):
    """
    Serializer for Todo for updating batch or multiple Todo Ordering
    """

    def update_obj_instance(self, instance, validated_data):
        todo_result = []
        fields = []

        update_obj = list(zip(instance, validated_data))
        for objs in update_obj:
            ins, obj = list(objs)
            for attrs in list(obj.keys()):
                ins.attrs = obj[attrs]
            todo_result.append(ins)
            fields.extend(list(obj.keys()))
        return todo_result, fields

    def todo_view_update(self, instance, validated_data):
        todo_result, fields = self.update_obj_instance(instance, validated_data)

        try:
            self.child.Meta.model.objects.bulk_update(todo_result, list(set(fields)))
        except IntegrityError as e:
            raise serializers.ValidationError(detail=e)
        return todo_result

    def task_view_update(self, instance, validated_data):
        todo_last_added = [task.pop("todo_last_added", None) for task in validated_data]

        task_result, fields = self.update_obj_instance(instance, validated_data)
        todo_list = []
        for i, task in enumerate(task_result):
            if todo_last_added[i]:
                task.todo.last_added = todo_last_added[i]
                todo_list.append(task.todo)
        try:
            self.child.Meta.model.objects.bulk_update(task_result, fields)
        except IntegrityError as e:
            raise serializers.ValidationError(detail=e)
        if todo_list:
            try:
                Todo.objects.bulk_update(todo_list, ["last_added"])
            except IntegrityError as e:
                raise serializers.ValidationError(detail=e)
        return task_result

    def update(self, instance, validated_data):
        """
        Update Model Orderings
        """
        view_name = self.context["view"].view_name()
        [obj.pop("id", None) for obj in validated_data]

        if view_name == "todo":
            return self.todo_view_update(instance, validated_data)

        if view_name == "task":
            return self.task_view_update(instance, validated_data)

    class Meta:
        fields = ["id", "ordering"]
        read_only_fields = ["id"]


class BatchCreateSerializer(BatchCreateSerializerMixin, serializers.ListSerializer):
    """
    Serializer for performing batch create
    """

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

        except IntegrityError as e:
            raise serializers.ValidationError(detail=e)

    def todo_view_create(self, validated_data):
        tasks = [task_field.pop("tasks", None) for task_field in validated_data]

        todo_result = [self.child.Meta.model(**attrs) for attrs in validated_data]
        self.increment_obj_ordering_todo(todo_result)

        try:
            self.child.Meta.model.objects.bulk_create(todo_result)

        except IntegrityError as e:
            raise serializers.ValidationError(detail=e)

        self.assign_bulk_tasks_todo_id(tasks, todo_result)

        return todo_result

    def task_view_create(self, validated_data):
        todo_last_added = [task.pop("todo_last_added", None) for task in validated_data]

        task_result = [self.child.Meta.model(**task) for task in validated_data]

        self.increment_obj_ordering_task(task_result)

        todo_list = []

        for i, task in enumerate(task_result):
            if todo_last_added[i]:
                task.todo.last_added = todo_last_added[i]
                todo_list.append(task.todo)

        try:
            self.child.Meta.model.objects.bulk_create(task_result)
        except IntegrityError as e:
            raise serializers.ValidationError(detail=e)

        if todo_list:
            try:
                Todo.objects.bulk_update(todo_list, ["last_added"])
            except IntegrityError as e:
                raise serializers.ValidationError(detail=e)

        return task_result

    def create(self, validated_data):
        view_name = self.context["view"].view_name()

        if view_name == "todo":
            return self.todo_view_create(validated_data)

        if view_name == "task":
            return self.task_view_create(validated_data)

    class Meta:
        fields = ["id", "title", "tasks", "last_added", "completed", "ordering"]
        read_only_fields = ["id", "ordering"]


class SerializerGetListSerializerClassInitMixin:
    """
    Mixin to allow setting the list_serializer_class for a serializer
    """

    list_serializer_type_classes = {
        "batch_update": BatchUpdateSerializer,
        "batch_update_ordering": BatchOrderingUpdateSerializer,
        "batch_create": BatchCreateSerializer,
    }

    def __init__(self, *args, **kwargs):
        list_serializer_type = kwargs.pop("type", None)

        view_name = kwargs.pop("view_name", None)

        if view_name == "todo":
            if list_serializer_type == "batch_create":
                self.Meta.read_only_fields = ["id", "ordering"]
            else:
                self.Meta.read_only_fields = ["id", "last_added", "ordering"]
        if view_name == "task":
            if list_serializer_type == "batch_create":
                self.Meta.read_only_fields = ["ordering"]
            else:
                self.Meta.read_only_fields = ["todo_last_added", "ordering"]

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

        if todo is not None:
            task = Task.objects.create(
                todo=todo,
                task=validated_data["task"],
                completed=validated_data["completed"],
            )
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
