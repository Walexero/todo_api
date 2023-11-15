from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample


class BatchSerializerMixin:
    """
    Mixin to be subclassed by all batch related serializers mixins
    """

    def to_internal_value(self, data):
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


class BatchUpdateSerializerMixin(BatchSerializerMixin):
    """
    Mixin to be used with updating the properties of a model
    to update
    """

    def passes_test(self):
        test = self.context["request"].method == "PATCH"
        test &= self.context.get("batch_update", False)
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
            "batch_update",
        ]:
            context[self.action] = True
        return context

    def validate_ids(self, data, field="id", unique=True, return_unique=False):
        if isinstance(data, list):
            id_list = [int(i[field]) for i in data]

            if unique and len(id_list) != len(set(id_list)):
                raise ValidationError(
                    "Cannot make multiple request operation on a single instance"
                )

            if return_unique:
                return list(set(id_list))

            return id_list

        return [data]

    def validate_delete_ids(self, data):
        if isinstance(data, list):
            for i in data:
                if not isinstance(i, int):
                    raise ValidationError("Int is required as field value")

            return list(set(data))
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

    def validate_titles(self, data, field="title"):
        if isinstance(data, list):
            for i in data:
                if title := i.get("title", None):
                    if not isinstance(title, str):
                        raise ValidationError(
                            "Only strings are allowed as title value "
                        )
                pass
        return [data]

    def validate_completed(self, data, field="completed"):
        if isinstance(data, list):
            for i in data:
                if completed := i.get("completed", None):
                    if not isinstance(completed, bool):
                        raise ValidationError(
                            "Only bools are allowed as completed value "
                        )
                pass
        return [data]


class BatchUpdateOrderingRouteMixin:  # (BatchRouteMixin):
    """
    Mixin that adds a  `batch_update_ordering` API route to a viewset. To be used with BatchUpdateOrderingSerializerMixin
    """

    @action(detail=False, methods=["PATCH"], url_name="batch_update_ordering")
    def batch_update_ordering(self, request, *args, **kwargs):
        try:
            ids = self.validate_ids(request.data["ordering_list"])
            self.validate_orderings(request.data["ordering_list"])

            queryset = self.filter_queryset(self.get_queryset(ids=ids))
            serializer = self.get_serializer(
                queryset,
                data=request.data["ordering_list"],
                partial=True,
                many=True,
                type=self.action,
                view_name=self.view_name(),
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(e)


class BatchUpdateRouteMixin:
    """
    Mixin that adds a  `batch_update` API route to a viewset. To be used with BatchUpdateSerializerMixin
    """

    @action(detail=False, methods=["PATCH"], url_name="batch_update")
    def batch_update(self, request, *args, **kwargs):
        try:
            ids = self.validate_ids(request.data["update_list"])
            self.validate_titles(request.data["update_list"])
            self.validate_completed(request.data["update_list"])

            queryset = self.filter_queryset(self.get_queryset(ids=ids))

            serializer = self.get_serializer(
                queryset,
                data=request.data["update_list"],
                partial=True,
                many=True,
                type=self.action,
                view_name=self.view_name(),
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            raise ValidationError(e)


class BatchCreateRouteMixin:  # (BatchRouteMixin):
    """
    Mixin that adds a  `batch_create` API route to a viewset
    """

    @action(detail=False, methods=["POST"], url_name="batch_create")
    def batch_create(self, request, *args, **kwargs):
        try:
            queryset = self.get_object()

            serializer = self.get_serializer(
                queryset,
                data=request.data["create_list"],
                many=True,
                type=self.action,
                view_name=self.view_name(),
            )
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise ValidationError(e)


class BatchDeleteRouteMixin:
    """
    Mixin that adds a  `batch_delete` API route to a viewset
    """

    @action(detail=False, methods=["DELETE"], url_name="batch_delete")
    def batch_delete(self, request, *args, **kwargs):
        try:
            ids = self.validate_delete_ids(request.data["delete_list"])
            print("the deel ids", ids)

            queryset = self.filter_queryset(self.get_queryset(ids=ids))
            queryset.delete()
            return Response(
                self.serializer_class(queryset, many=True).data,
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            raise ValidationError(e)
