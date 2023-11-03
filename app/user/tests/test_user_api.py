"""
Test for the User API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")
CHANGE_PASSWORD_URL = reverse("user:change_password")
USER_UPDATE_INFO = reverse("user:update_info")


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
        }

    def test_create_user_success(self):
        """
        Test creating a user is successful
        """

        # user = create_user(payload)

        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.payload["email"])

        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_email_exists_error(self):
        """
        Test error returned if user with email exists
        """
        create_user(**self.payload)
        payload = {
            "first_name": "TestUser",
            "last_name": "User",
            "email": self.payload["email"],
            "password": self.payload["password"],
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
        user = create_user(**self.payload)
        user.is_active = True
        user.save()
        payload = {"email": self.payload["email"], "password": ""}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", "")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorize(self):
        """
        Test authentication is required for users
        """
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


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
            "password": "updatedUser123",
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # payload.pop("password")
        self.assertTrue(self.user.check_password(payload["password"]))
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
