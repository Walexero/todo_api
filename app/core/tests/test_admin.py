from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Tests for Django admin"""

    def setUp(self):
        """
        Create Test Admin User and Test User for admin
        """
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="Awesomeuser123"
        )
        self.admin_user.is_active = True
        self.admin_user.save()

        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="Awesomeuser123",
            first_name="Test",
            last_name="User",
        )

        self.user.is_active = True
        self.user.save()

    def test_users_lists(self):
        """Test that users are listed on page"""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.first_name)
        self.assertContains(res, self.user.email)

    def test_edit_user_page(self):
        """
        Test the edit user page works
        """
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """
        Test thee create user page works
        """
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
