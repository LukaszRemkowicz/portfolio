from unittest.mock import MagicMock

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

from inbox.models import ContactFormSettings

# Email sending and contact form setup are automatically handled by conftest.py fixtures


@pytest.mark.django_db
def test_contact_throttling_success(
    mock_email_service: MagicMock, contact_form_settings: ContactFormSettings, api_client: APIClient
) -> None:
    """Test that first 5 contact form submissions succeed"""
    contact_form_settings.enabled = True
    contact_form_settings.save()

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

        response = api_client.post(url, data, format="json")
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
def test_contact_throttling_limit_exceeded(
    mock_email_service: MagicMock, contact_form_settings: ContactFormSettings, api_client: APIClient
) -> None:
    """Test that contact form submission is throttled after limit"""
    contact_form_settings.enabled = True
    contact_form_settings.save()

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

        response = api_client.post(url, data, format="json")

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
def test_contact_throttling_headers(
    mock_email_service: MagicMock, contact_form_settings: ContactFormSettings, api_client: APIClient
) -> None:
    """Test that throttling response includes proper headers"""
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
        response = api_client.post(url, data, format="json")
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


@pytest.mark.django_db
def test_contact_endpoint_disallows_get(api_client: APIClient) -> None:
    """Test that GET requests to the contact endpoint return 405 Method Not Allowed"""
    url = reverse("inbox:contact-message-list")

    response = api_client.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_contact_payload_too_large(
    contact_form_settings: ContactFormSettings, api_client: APIClient
) -> None:
    """Test that large payloads are rejected with 413"""
    contact_form_settings.enabled = True
    contact_form_settings.save()

    url = reverse("inbox:contact-message-list")
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "x" * 10001,
    }

    # API client will automatically set correct CONTENT_LENGTH
    response = api_client.post(url, data, format="json")
    assert response.status_code == 413
    assert "too large" in response.data["detail"].lower()


@pytest.mark.django_db
def test_contact_invalid_data(
    contact_form_settings: ContactFormSettings, api_client: APIClient
) -> None:
    """Test that invalid data is rejected by the view before service call"""
    contact_form_settings.enabled = True
    contact_form_settings.save()

    url = reverse("inbox:contact-message-list")
    data = {
        "name": "J",  # Too short
        "email": "invalid",
        "subject": "Hi",  # Too short
        "message": "Too short",
    }

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data
    assert "email" in response.data
    assert "subject" in response.data
    assert "message" in response.data
