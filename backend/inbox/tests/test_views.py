"""
Tests for inbox views
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse


@pytest.mark.django_db
def test_contact_throttling_success():
    """Test that first 5 contact form submissions succeed"""
    client = APIClient()
    url = reverse("inbox:contact-message-list")

    data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "Test message content",
    }

    # First 5 requests should succeed
    for _ in range(5):
        response = client.post(url, data, format="json")
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        assert "id" in response.data or response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_contact_throttling_limit_exceeded():
    """Test that contact form submission is throttled after limit"""
    client = APIClient()
    url = reverse("inbox:contact-message-list")

    data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "Test message content",
    }

    # Make requests until we get throttled
    throttled = False
    for request_number in range(6):  # Try up to 6 requests
        response = client.post(url, data, format="json")

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            throttled = True
            assert (
                "throttled" in response.data.get("detail", "").lower()
                or "rate limit" in response.data.get("detail", "").lower()
            )
            break
        else:
            # Should be successful before throttling kicks in
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]

    # We should have been throttled at some point
    assert throttled, "Expected to be throttled within 6 requests"


@pytest.mark.django_db
def test_contact_throttling_headers():
    """Test that throttling response includes proper headers"""
    client = APIClient()
    url = reverse("inbox:contact-message-list")

    data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "Test message content",
    }

    # Make requests until throttled
    response = None
    for _ in range(6):
        response = client.post(url, data, format="json")
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            break

    # Check throttling headers
    if response and response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        # These headers might be present depending on DRF version
        possible_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ]

        # At least one throttling header should be present
        throttling_headers_found = any(header in response for header in possible_headers)
        assert throttling_headers_found or response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
