# backend/users/tests/test_axes.py
import pytest
from axes.models import AccessAttempt

from django.contrib.auth import get_user_model
from django.urls import reverse

from users.tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestAxesLockout:
    def setup_method(self):
        # Ensure we have a clean state for each test
        AccessAttempt.objects.all().delete()
        self.login_url = reverse("admin:login")
        self.password = "testpassword123"
        # We need a superuser because axes is configured for admin
        self.user = UserFactory.create_superuser(email="testadmin@example.com")
        self.user.set_password(self.password)
        self.user.save()

    def test_failed_login_increments_failures_count(self, client):
        """Test that failed login attempts increment the failures_since_start in AccessAttempt."""
        for i in range(3):
            client.post(
                self.login_url,
                {
                    "username": self.user.email,
                    "password": "wrongpassword",
                },
            )
            attempt = AccessAttempt.objects.get(username=self.user.email)
            assert attempt.failures_since_start == i + 1

    def test_lockout_after_failure_limit(self, client):
        """Test that the user is locked out after AXES_FAILURE_LIMIT (5) attempts."""
        # Perform 5 failed attempts
        for _ in range(5):
            client.post(
                self.login_url,
                {
                    "username": self.user.email,
                    "password": "wrongpassword",
                },
            )

        # 6th attempt should be blocked (429 Too Many Requests by default in this version)
        response = client.post(
            self.login_url,
            {
                "username": self.user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 429

    def test_reset_on_successful_login(self, client):
        """Test that a successful login resets the failure count."""
        # 3 failed attempts
        for _ in range(3):
            client.post(
                self.login_url,
                {
                    "username": self.user.email,
                    "password": "wrongpassword",
                },
            )

        attempt = AccessAttempt.objects.get(username=self.user.email)
        assert attempt.failures_since_start == 3

        # 1 successful login
        response = client.post(
            self.login_url,
            {
                "username": self.user.email,
                "password": self.password,
            },
            follow=False,
        )

        assert response.status_code == 302
        # AccessAttempt should be deleted on success (AXES_RESET_ON_SUCCESS = True)
        assert not AccessAttempt.objects.filter(username=self.user.email).exists()

    def test_non_existent_user_is_also_tracked(self, client):
        """Test that attempts for non-existent users are also tracked."""
        fake_email = "nonexistent@example.com"
        for _ in range(2):
            client.post(
                self.login_url,
                {
                    "username": fake_email,
                    "password": "somepassword",
                },
            )

        attempt = AccessAttempt.objects.get(username=fake_email)
        assert attempt.failures_since_start == 2
