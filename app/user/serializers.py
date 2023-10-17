"""
Serializers for the User API view
"""
import uuid

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import make_password
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User Object
    """

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """
        Create and return a user with encrypted password
        """
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """
        Update the User Instance and return it
        """
        password = validated_data.pop("password")
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """
    Serializer for the user auth token
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        """
        Validate and authenticate the user
        """
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            self.context.get("request"), username=email, password=password
        )

        if user:
            attrs["user"] = user
            return attrs

        raise serializers.ValidationError(
            _("Unable to authenticate user"), code="authorization"
        )
