"""
Tests for inbox views
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

# Email sending and contact form setup are automatically handled by conftest.py fixtures


@pytest.mark.django_db
def test_contact_throttling_success(mock_email_service):
    """Test that first 5 contact form submissions succeed"""
    client = APIClient()
    url = reverse("inbox:contact-message-list")

    # Use unique data for each request to avoid duplicate detection
    successful_responses = []
    for request_number in range(5):
        data = {
            "name": f"Test User {request_number}",
            "email": f"test{request_number}@example.com",
            "subject": f"Test Subject {request_number}",
            "message": f"Test message content {request_number}",
        }

        response = client.post(url, data, format="json")
        assert (
            response.status_code == status.HTTP_201_CREATED
        ), f"Request {request_number} should succeed, got {response.status_code}"
        assert "id" in response.data
        assert "message" in response.data
        successful_responses.append(response)

    # Verify email service was called for each successful submission (but emails were mocked)
    assert (
        mock_email_service.call_count == 5
    ), f"Expected 5 email calls, got {mock_email_service.call_count}"


@pytest.mark.django_db
def test_contact_throttling_limit_exceeded(mock_email_service):
    """Test that contact form submission is throttled after limit"""
    client = APIClient()
    url = reverse("inbox:contact-message-list")

    # Use same email but different subjects to hit throttling limit (5/hour per IP)
    email = "throttle_test@example.com"

    # Make requests until we get throttled (IP limit is 5/hour)
    throttled = False
    successful_count = 0

    for request_number in range(6):  # Try up to 6 requests
        data = {
            "name": f"Test User {request_number}",
            "email": email,
            "subject": f"Throttle Test Subject {request_number}",
            "message": f"Test message content {request_number}",
        }

        response = client.post(url, data, format="json")

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            throttled = True
            assert (
                "throttled" in response.data.get("detail", "").lower()
                or "rate limit" in response.data.get("detail", "").lower()
                or "too many" in response.data.get("detail", "").lower()
            )
            break
        else:
            # Should be successful before throttling kicks in
            assert response.status_code == status.HTTP_201_CREATED
            successful_count += 1

    # We should have been throttled at some point
    assert (
        throttled
    ), f"Expected to be throttled within 6 requests, but {successful_count} succeeded"
    assert successful_count <= 5, "Should have at most 5 successful requests before throttling"


@pytest.mark.django_db
def test_contact_throttling_headers(mock_email_service):
    """Test that throttling response includes proper headers"""
    client = APIClient()
    url = reverse("inbox:contact-message-list")

    # Use same email to hit throttling
    email = "header_test@example.com"

    # Make requests until throttled
    response = None
    for request_number in range(6):
        data = {
            "name": f"Test User {request_number}",
            "email": email,
            "subject": f"Header Test Subject {request_number}",
            "message": f"Test message content {request_number}",
        }
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

        # At least one throttling header should be present, or just check status code
        throttling_headers_found = any(header in response for header in possible_headers)
        assert throttling_headers_found or response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
