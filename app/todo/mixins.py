from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError


class BatchSerializerMixin:
    """
    Mixin to be subclassed by all batch related serializers mixins
    """

    def to_internal_value(self, data):
        print("the data", data)
        # ret = super().to_internal_value(data)
        if not isinstance(data, list):
            raise ValidationError("Invalid Data Supplied,a List is expected")

        if self.passes_test():
            return data
        raise ValidationError("Could not validate request data")


class BatchUpdateOrderingSerializerMixin(BatchSerializerMixin):
    """
    Mixin to be used with updating the ordering of the
    TodoBatchUpdateOrderingSerializer. Only for ordering
    """

    def passes_test(self):
        test = self.context["request"].method == "PATCH"
        test &= self.context.get("batch_update_ordering", False)
        return test


class BatchUpdateAllSerializerMixin(BatchSerializerMixin):
    """
    Mixin to be used with updating the properties of a model
    to update
    """

    def passes_test(self):
        test = self.context["request"].method == "PATCH"
        test &= self.context.get("batch_update_all", False)
        return test


class BatchCreateSerializerMixin(BatchSerializerMixin):
    """
    Mixin to be used with creating batch models
    """

    def passes_test(self):
        test = self.context["request"].method == "POST"
        test &= self.context.get("batch_create", False)
        return test


class BatchDeleteSerializerMixin(BatchSerializerMixin):
    """
    Mixin to be used with deleting batch models
    """

    def passes_test(self):
        test = self.context["request"].method == "DELETE"
        test &= self.context.get("batch_delete", False)
        return test


class BatchRouteMixin:
    """
    Mixin to be subclassed by all batch route related mixins
    """

    # action_name = ""

    def get_object(self):
        # Override to return None if the lookup_url_kwargs is not present
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        return

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        # batchRoute name set through class var
        context = super().get_serializer_context()

        if self.action in [
            "batch_update_ordering",
            "batch_create",
            "batch_delete",
            "batch_update_all",
        ]:  # == self.action_name:
            # print("the action name", self.action_name)
            context[self.action] = True
        return context

    # def validate_ids(self, data, field="id", unique=True):
    #     if isinstance(data, list):
    #         id_list = [int(i["id"]) for i in data]

    #         if unique and len(id_list) != len(set(id_list)):
    #             raise ValidationError(
    #                 "Cannot make multiple request operation on a single instance"
    #             )

    #         return id_list

    #     return [data]

    # def validate_orderings(self, data, field="ordering", unique=True):
    #     if isinstance(data, list):
    #         ordering_list = [int(i["ordering"]) for i in data]

    #         if unique and len(ordering_list) != len(set(ordering_list)):
    #             raise ValidationError(
    #                 "Cannot assign same ordering to multiple instance"
    #             )
    #         return ordering_list


class BatchUpdateOrderingRouteMixin:  # (BatchRouteMixin):
    """
    Mixin that adds a  `batch_update_ordering` API route to a viewset. To be used with BatchUpdateOrderingSerializerMixin
    """

    # action_name = "batch_update_ordering"

    @action(detail=False, methods=["PATCH"], url_name="batch_update_ordering")
    def batch_update_ordering(self, request, *args, **kwargs):
        ids = self.validate_ids(request.data["ordering_list"])
        self.validate_orderings(request.data["ordering_list"])

        queryset = self.filter_queryset(self.get_queryset(ids=ids))
        serializer = self.get_serializer(
            queryset,
            data=request.data["ordering_list"],
            partial=True,
            many=True,
            type=self.action,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def validate_ids(self, data, field="id", unique=True):
        if isinstance(data, list):
            id_list = [int(i["id"]) for i in data]

            if unique and len(id_list) != len(set(id_list)):
                raise ValidationError(
                    "Cannot make multiple request operation on a single instance"
                )

            return id_list

        return [data]

    def validate_orderings(self, data, field="ordering", unique=True):
        if isinstance(data, list):
            ordering_list = [int(i["ordering"]) for i in data]

            if unique and len(ordering_list) != len(set(ordering_list)):
                raise ValidationError(
                    "Cannot assign same ordering to multiple instance"
                )
            return ordering_list

        return [data]


class BatchUpdateAllRouteMixin(BatchRouteMixin):
    """
    Mixin that adds a  `batch_update_all` API route to a viewset. To be used with BatchUpdateAllSerializerMixin
    """

    action_name = "batch_update_all"

    @action(detail=False, methods=["PATCH"], url_name="batch_update_all")
    def batch_update_all(self, request, *args, **kwargs):
        ids = self.validate_ids(request.data["update_list"])

        queryset = self.filter_queryset(self.get_queryset(ids=ids))

        serializer = self.get_serializer(
            queryset,
            data=request.data["update_list"],
            partial=True,
            many=True,
            type=self.action_name,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BatchCreateRouteMixin:  # (BatchRouteMixin):
    """
    Mixin that adds a  `batch_create` API route to a viewset
    """

    # action_name = "batch_create"

    @action(detail=False, methods=["POST"], url_name="batch_create")
    def batch_create(self, request, *args, **kwargs):
        # print("in the batch_create", self.action_type)
        todo = self.get_object()
        serializer = self.get_serializer(
            todo,
            data=request.data["create_list"],
            many=True,
            type=self.action,
            user=request.user,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BatchDeleteRouteMixin(BatchRouteMixin):
    """
    Mixin that adds a  `batch_delete` API route to a viewset
    """

    action_name = "batch_delete"

    @action(detail=False, methods=["PATCH"], url_name="batch_delete")
    def batch_delete(self, request, *args, **kwargs):
        ids = self.validate_ids(request.data["delete_list"])

        queryset = self.filter_queryset(self.get_queryset(ids=ids))

        serializer = self.get_serializer(
            queryset,
            data=request.data["delete_list"],
            many=True,
            type=self.action_name,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_delete(serializer)
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
