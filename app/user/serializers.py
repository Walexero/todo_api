"""
Serializers for the User API view
"""
import uuid

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
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
        password = validated_data.pop("password", None)
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


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ["old_password", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                {"old_password": "Old password is not correct"}
            )
        return value

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if user.pk != instance.pk:
            raise serializers.ValidationError(
                _("Unable to authenticate request"), code="authorization"
            )
        instance.set_password(validated_data["password"])
        instance.save()

        return instance


class UpdateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value):
        user = self.context["request"].user
        if self.Meta.model.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError({"email": "This email is already in use"})
        return value

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if user.pk != instance.pk:
            raise serializers.ValidationError(
                _("Unable to authenticate request"), code="authorization"
            )
        instance.first_name = validated_data["first_name"]
        instance.last_name = validated_data["last_name"]
        instance.email = validated_data["email"]

        instance.save()

        return instance
