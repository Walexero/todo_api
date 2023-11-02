from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError


class BatchUpdateSerializerMixin:
    """
    Mixin to be used with the TodoBatchUpdateOrderingSeriazer
    """

    def passes_test(self):
        test = self.context["request"].method == "PATCH"
        test &= self.context.get("batch_update", False)
        return test

    def to_internal_value(self, data):
        # ret = super().to_internal_value(data)
        if not isinstance(data, list):
            raise ValidationError("Invalid Data Supplied,a Dict is expected")

        if self.passes_test():
            return data


class BatchUpdateRouteMixin:
    """
    Mixin that adds a  `batch_update` API route to a viewset. To be used with BatchUpdateSerializerMixin & A Serializer that has the BatchUpdateSerializerMixin as a mixin
    """

    def get_object(self):
        # Override to return None if the lookup_url_kwargs is not present
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        return

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        # Add `batch_update` flag to the serializer context to get the batch_update data
        context = super().get_serializer_context()
        if self.action == "batch_update":
            context["batch_update"] = True
        return context

    @action(detail=False, methods=["PATCH"], url_name="batch_update")
    def batch_update(self, request, *args, **kwargs):
        ids = self.validate_ids(request.data["ordering_list"])
        self.validate_orderings(request.data["ordering_list"])

        queryset = self.filter_queryset(self.get_queryset(ids=ids))
        serializer = self.get_serializer(
            queryset, data=request.data["ordering_list"], partial=True, many=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def validate_ids(self, data, field="id", unique=True):
        if isinstance(data, list):
            id_list = [int(i["id"]) for i in data]

            if unique and len(id_list) != len(set(id_list)):
                raise ValidationError("Cannot make multiple updates to a single todo")

            return id_list

        return [data]

    def validate_orderings(self, data, field="ordering", unique=True):
        if isinstance(data, list):
            ordering_list = [int(i["ordering"]) for i in data]

            if unique and len(ordering_list) != len(set(ordering_list)):
                raise ValidationError("Cannot assign same ordering to multiple Todos")
            return ordering_list
