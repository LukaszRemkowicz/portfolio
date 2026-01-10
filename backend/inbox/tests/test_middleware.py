# backend/inbox/tests/test_middleware.py
"""
Tests for contact form kill switch middleware
"""

from unittest.mock import patch

import pytest

from django.http import JsonResponse

# Middleware, request_factory, and contact_form_settings fixtures are provided by conftest.py


@pytest.mark.django_db
def test_middleware_allows_post_when_enabled(middleware, request_factory, contact_form_settings):
    """Test middleware allows POST requests when form is enabled"""
    contact_form_settings.enabled = True
    contact_form_settings.save()

    request = request_factory.post("/api/v1/contact/")
    response = middleware.process_request(request)

    assert response is None, "Middleware should allow request when enabled"


@pytest.mark.django_db
def test_middleware_blocks_post_when_disabled(middleware, request_factory, contact_form_settings):
    """Test middleware blocks POST requests when form is disabled"""
    contact_form_settings.enabled = False
    contact_form_settings.save()

    request = request_factory.post("/api/v1/contact/")
    response = middleware.process_request(request)

    assert response is not None, "Middleware should block request when disabled"
    assert isinstance(response, JsonResponse), "Response should be JsonResponse"
    assert response.status_code == 400, "Should return HTTP 400 Bad Request"

    import json

    response_data = json.loads(response.content)
    assert "message" in response_data
    assert "disabled" in response_data["message"].lower()


@pytest.mark.django_db
def test_middleware_ignores_non_post_requests(middleware, request_factory, contact_form_settings):
    """Test middleware ignores GET, PUT, DELETE, etc. requests"""
    contact_form_settings.enabled = False  # Disabled, but should still allow non-POST
    contact_form_settings.save()

    for method in ["GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        request = getattr(request_factory, method.lower())("/api/v1/contact/")
        response = middleware.process_request(request)
        assert response is None, f"Middleware should ignore {method} requests"


@pytest.mark.django_db
def test_middleware_only_checks_contact_endpoint(
    middleware, request_factory, contact_form_settings
):
    """Test middleware only checks contact endpoint, ignores other paths"""
    contact_form_settings.enabled = False  # Disabled
    contact_form_settings.save()

    other_paths = [
        "/api/v1/profile/",
        "/api/v1/image/",
        "/api/v1/admin/",
        "/api/v1/contact-messages/",  # Different endpoint
        "/api/v1/contact",  # Missing trailing slash (not router path)
        "/api/v1/contact/123/",  # Detail endpoint (not base endpoint)
        "/",
    ]

    for path in other_paths:
        request = request_factory.post(path)
        response = middleware.process_request(request)
        assert response is None, f"Middleware should ignore path: {path}"


@pytest.mark.django_db
def test_middleware_only_checks_exact_router_path(
    middleware, request_factory, contact_form_settings
):
    """Test middleware only checks exact DRF router path with trailing slash"""
    contact_form_settings.enabled = False
    contact_form_settings.save()

    # DRF router always creates URLs with trailing slashes: /api/v1/contact/
    exact_router_path = "/api/v1/contact/"
    path_without_slash = "/api/v1/contact"

    # Exact router path should be blocked when disabled
    request_with_slash = request_factory.post(exact_router_path)
    response_with_slash = middleware.process_request(request_with_slash)
    assert response_with_slash is not None, "Should block exact router path when disabled"
    assert response_with_slash.status_code == 400

    # Path without trailing slash is not the router path, so should be ignored (not blocked)
    # This lets Django's URL resolver handle it (will return 404 or redirect)
    request_without_slash = request_factory.post(path_without_slash)
    response_without_slash = middleware.process_request(request_without_slash)
    assert (
        response_without_slash is None
    ), "Should ignore path without trailing slash (not router path)"


@pytest.mark.django_db
def test_middleware_fails_open_on_settings_error(middleware, request_factory):
    """Test middleware fails open (allows request) if settings check fails"""
    request = request_factory.post("/api/v1/contact/")

    # Mock get_settings to raise an exception
    with patch(
        "inbox.middleware.ContactFormSettings.get_settings", side_effect=Exception("Database error")
    ):
        response = middleware.process_request(request)
        assert response is None, "Middleware should fail open (allow request) on error"


@pytest.mark.django_db
def test_middleware_logs_blocked_requests(
    middleware, request_factory, contact_form_settings, caplog
):
    """Test middleware logs blocked requests"""
    import logging

    caplog.set_level(logging.WARNING)

    contact_form_settings.enabled = False
    contact_form_settings.save()

    request = request_factory.post("/api/v1/contact/")
    response = middleware.process_request(request)

    assert response is not None
    assert any("blocked" in record.message.lower() for record in caplog.records)
    assert any("disabled" in record.message.lower() for record in caplog.records)


@pytest.mark.django_db
def test_middleware_logs_errors(middleware, request_factory, caplog):
    """Test middleware logs errors when settings check fails"""
    import logging

    caplog.set_level(logging.ERROR)

    request = request_factory.post("/api/v1/contact/")

    with patch(
        "inbox.middleware.ContactFormSettings.get_settings", side_effect=Exception("Database error")
    ):
        middleware.process_request(request)

    assert any("error" in record.message.lower() for record in caplog.records)
    assert any("settings" in record.message.lower() for record in caplog.records)


@pytest.mark.django_db
def test_middleware_extracts_client_ip(middleware, request_factory, contact_form_settings, caplog):
    """Test middleware correctly extracts client IP for logging"""
    import logging

    caplog.set_level(logging.WARNING)

    contact_form_settings.enabled = False
    contact_form_settings.save()

    # Test with X-Forwarded-For header (proxy scenario)
    request = request_factory.post("/api/v1/contact/", HTTP_X_FORWARDED_FOR="192.168.1.1, 10.0.0.1")
    response = middleware.process_request(request)

    assert response is not None
    # IP should be logged (first IP from X-Forwarded-For)
    log_messages = " ".join([record.message for record in caplog.records])
    assert "192.168.1.1" in log_messages or "IP:" in log_messages


@pytest.mark.django_db
def test_middleware_handles_missing_x_forwarded_for(
    middleware, request_factory, contact_form_settings
):
    """Test middleware handles requests without X-Forwarded-For header"""
    contact_form_settings.enabled = False
    contact_form_settings.save()

    request = request_factory.post("/api/v1/contact/")
    # Ensure REMOTE_ADDR is set
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    if "HTTP_X_FORWARDED_FOR" in request.META:
        del request.META["HTTP_X_FORWARDED_FOR"]

    response = middleware.process_request(request)
    assert response is not None
    assert response.status_code == 400
