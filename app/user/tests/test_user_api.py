"""
Test for the User API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from rest_framework.authtoken.models import Token

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")
CHANGE_PASSWORD_URL = reverse("user:change_password")
USER_UPDATE_INFO = reverse("user:update_info")
TODO_URL = reverse("todo:todo-list")
RESET_PWD_URL = reverse("user:password_reset")


def create_user(**params):
    """Create and return a user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """
    Test the public features of the user API
    """

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": "user@example.com",
            "password": "Awesomeuser123",
            "password2": "Awesomeuser123",
        }

    def test_create_user_success(self):
        """
        Test creating a user is successful
        """

        # user = create_user(payload)
        self.payload["password2"] = self.payload["password"]
        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.payload["email"])

        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_without_matching_password_failure(self):
        """
        Test creating a user fails if the password doesn't match
        """

        # user = create_user(payload)
        self.payload["password2"] = "ldksjfldsjflasd"
        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_with_email_exists_error(self):
        """
        Test error returned if user with email exists
        """
        self.payload.pop("password2")
        create_user(**self.payload)
        payload = {
            "first_name": "TestUser",
            "last_name": "User",
            "email": self.payload["email"],
            "password": self.payload["password"],
            "password2": self.payload["password"],
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """
        Test an error is returned if password less than 5 chars
        """
        payload = self.payload.copy()
        payload["password"] = "User"

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """
        Test generates token for valid credentials
        """
        self.payload.pop("password2")
        user = create_user(**self.payload)
        user.is_active = True
        user.save()

        payload = {"email": self.payload["email"], "password": self.payload["password"]}

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """
        Test against creating token for bad credentials
        """
        self.payload.pop("password2")
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        payload = {"email": self.payload["email"], "password": "badpassword"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """
        Test posting a blank password returns an Error
        """
        self.payload.pop("password2")
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        payload = {"email": self.payload["email"], "password": ""}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", "")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_expiration_elapse_expires_token(self):
        """
        Test that the created token after its expiration timeframe expires
        """
        self.payload.pop("password2")
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        payload = {"email": self.payload["email"], "password": self.payload["password"]}
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_token = res.data["token"]

        token = Token.objects.get(user=user)
        token.created = timezone.now() - timedelta(3)

        res_get_todos = self.client.get(
            TODO_URL,
            HTTP_AUTHORIZATION=res_token,
        )
        self.assertEqual(
            res_get_todos.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_token_and_expire_token_and_token_updated_when_new_token_requested(
        self,
    ):
        """
        Test that a new token is created after a token has expired
        """
        self.payload.pop("password2")
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        payload = {"email": self.payload["email"], "password": self.payload["password"]}
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_token = res.data["token"]

        token = Token.objects.get(user=user)
        token.created = timezone.now() - timedelta(3)
        token.save()

        res_get_todos = self.client.get(TODO_URL, HTTP_AUTHORIZATION=res_token)
        self.assertEqual(
            res_get_todos.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        res_new_token = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotEqual(res_new_token.data["token"], res_token)
        # self.assertTrue(res_new_token.data["token"] != res_token)

    def test_retrieve_user_unauthorize(self):
        """
        Test authentication is required for users
        """
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_password(self):
        """
        Test the reset password sends the reset email to the user
        """
        self.payload.pop("password2")
        user = create_user(**self.payload)

        reset_payload = {"email": self.payload["email"]}

        res = self.client.post(RESET_PWD_URL, reset_payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PrivateUserApiTests(TestCase):
    """
    Test User API requests that require authentication
    """

    def setUp(self):
        self.payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": "user@example.com",
            "password": "Awesomeuser123",
        }

        self.user = create_user(**self.payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """
        Test retreiving profile for logged in user
        """
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        user = self.payload.copy()
        user.pop("password")

        self.assertEqual(res.data, user)

    def test_post_me_not_allowed(self):
        """
        Test POST not allowed for the me endpoint
        """
        res = self.client.post(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """
        Test updating the user profile for the
        authenticated user
        """
        payload = {
            "first_name": "User",
            "last_name": "Updated",
            "email": "newemailforuser@example.com",
        }
        res = self.client.put(USER_UPDATE_INFO, payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # payload.pop("password")
        self.assertTrue(self.user.email == payload["email"])
        self.assertEqual(self.user.first_name, payload["first_name"])

    def test_password_change_for_authenticated_user_with_bad_credential(self):
        """
        Test that the authenticated user is able to change their password with bad credential
        """
        self.payload["email"] = "changepassword@example.com"
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        self.client.force_authenticate(user)

        payload = {
            "password": "Awesomeuser",
            "password2": "Awesomeuser",
            "old_password": "Awesomeuser",
        }

        res = self.client.put(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_for_authenticated_user_with_right_credential(self):
        """
        Test that the authenticated user is able to change their password with bad credential
        """
        self.payload["email"] = "changepassword@example.com"
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        self.client.force_authenticate(user)

        payload = {
            "password": "Awesomeuser",
            "password2": "Awesomeuser",
            "old_password": self.payload["password"],
        }

        res = self.client.put(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_change_password_to_current_password_fails(self):
        """
        Test that when a password is changed to the current password it
        fails
        """
        self.payload["email"] = "changepassword@example.com"
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        self.client.force_authenticate(user)

        payload = {
            "password": self.payload["password"],
            "password2": self.payload["password"],
            "old_password": self.payload["password"],
        }

        res = self.client.put(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_info_with_bad_credential(self):
        """
        Test that the user info cannot be updated with bad credentials
        """
        self.payload.pop("password")
        self.payload["email"] = "sdkfasdfksadjfsdf.com"

        res = self.client.put(USER_UPDATE_INFO, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_info_with_right_credential(self):
        """
        Test that the user info can be updated successfully
        """
        self.payload.pop("password")
        self.payload["email"] = "sdkfasdfksadjfsdf@email.com"

        res = self.client.put(USER_UPDATE_INFO, self.payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_change_password_without_matching_password_fails(self):
        """
        Test that the change password fails if the password and the confirm password do not match
        """
        payload = {"password": "Awesomeuser", "password2": "Aesomeuser"}

        res = self.client.put(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_matching_password_succeeds(self):
        """
        Test that the change password succeeds if the passwords match
        """
        payload = {
            "password": "Awesomeuser",
            "password2": "Awesomeuser",
            "old_password": self.payload["password"],
        }

        res = self.client.put(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
