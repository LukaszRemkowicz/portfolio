from unittest.mock import patch

import pytest

from django.db import DatabaseError
from django.http import JsonResponse
from django.test import RequestFactory

from core.models import LandingPageSettings
from inbox.middleware import ContactFormKillSwitchMiddleware

# Middleware, request_factory, and landing_page_settings fixtures are provided by conftest.py


@pytest.mark.django_db
def test_kill_switch_middleware_allows_post_when_enabled(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    landing_page_settings: LandingPageSettings,
) -> None:
    """Test kill_switch_middleware allows POST requests when form is enabled"""
    landing_page_settings.contact_form_enabled = True
    landing_page_settings.save()

    request = request_factory.post("/api/v1/contact/")
    response = kill_switch_middleware.process_request(request)

    assert response is None, "Middleware should allow request when enabled"


@pytest.mark.django_db
def test_kill_switch_middleware_blocks_post_when_disabled(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    landing_page_settings: LandingPageSettings,
) -> None:
    """Test kill_switch_middleware blocks POST requests when form is disabled"""
    landing_page_settings.contact_form_enabled = False
    landing_page_settings.save()

    request = request_factory.post("/api/v1/contact/")
    response = kill_switch_middleware.process_request(request)

    assert response is not None, "Middleware should block request when disabled"
    assert isinstance(response, JsonResponse), "Response should be JsonResponse"
    assert response.status_code == 400, "Should return HTTP 400 Bad Request"

    import json

    response_data = json.loads(response.content)
    assert "message" in response_data
    assert "disabled" in response_data["message"].lower()


@pytest.mark.django_db
def test_kill_switch_middleware_ignores_non_post_requests(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    landing_page_settings: LandingPageSettings,
) -> None:
    """Test kill_switch_middleware ignores GET, PUT, DELETE, etc. requests"""
    landing_page_settings.contact_form_enabled = False  # Disabled, but should still allow non-POST
    landing_page_settings.save()

    for method in ["GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        request = getattr(request_factory, method.lower())("/api/v1/contact/")
        response = kill_switch_middleware.process_request(request)
        assert response is None, f"Middleware should ignore {method} requests"


@pytest.mark.django_db
def test_kill_switch_middleware_only_checks_contact_endpoint(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    landing_page_settings: LandingPageSettings,
) -> None:
    """Test kill_switch_middleware only checks contact endpoint, ignores other paths"""
    landing_page_settings.contact_form_enabled = False  # Disabled
    landing_page_settings.save()

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
        response = kill_switch_middleware.process_request(request)
        assert response is None, f"Middleware should ignore path: {path}"


@pytest.mark.django_db
def test_kill_switch_middleware_only_checks_exact_router_path(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    landing_page_settings: LandingPageSettings,
) -> None:
    """Test kill_switch_middleware only checks exact DRF router path with trailing slash"""
    landing_page_settings.contact_form_enabled = False
    landing_page_settings.save()

    # DRF router always creates URLs with trailing slashes: /api/v1/contact/
    exact_router_path = "/api/v1/contact/"
    path_without_slash = "/api/v1/contact"

    # Exact router path should be blocked when disabled
    request_with_slash = request_factory.post(exact_router_path)
    response_with_slash = kill_switch_middleware.process_request(request_with_slash)
    assert response_with_slash is not None, "Should block exact router path when disabled"
    assert response_with_slash.status_code == 400

    # Path without trailing slash is not the router path, so should be ignored (not blocked)
    # This lets Django's URL resolver handle it (will return 404 or redirect)
    request_without_slash = request_factory.post(path_without_slash)
    response_without_slash = kill_switch_middleware.process_request(request_without_slash)
    assert (
        response_without_slash is None
    ), "Should ignore path without trailing slash (not router path)"


@pytest.mark.django_db
def test_kill_switch_middleware_fails_closed_on_settings_error(
    kill_switch_middleware: ContactFormKillSwitchMiddleware, request_factory: RequestFactory
) -> None:
    """Test kill_switch_middleware fails closed (blocks request) if settings check fails"""
    request = request_factory.post("/api/v1/contact/")

    # Mock DB error when accessing settings
    # Since we use LandingPageSettings.objects.first(), checking how to mock specific manager method
    # or just the model attribute access if possible.
    # Simplest is mocking the manager's first method.
    with patch(
        "core.models.LandingPageSettings.objects.first",
        side_effect=DatabaseError("Database error"),
    ):
        response = kill_switch_middleware.process_request(request)
        assert response is not None, "Middleware should fail closed (block request) on error"
        assert response.status_code == 500


@pytest.mark.django_db
def test_kill_switch_middleware_logs_blocked_requests(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    landing_page_settings: LandingPageSettings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test kill_switch_middleware logs blocked requests"""
    import logging

    caplog.set_level(logging.WARNING)

    landing_page_settings.contact_form_enabled = False
    landing_page_settings.save()

    request = request_factory.post("/api/v1/contact/")
    response = kill_switch_middleware.process_request(request)

    assert response is not None
    assert any("blocked" in record.message.lower() for record in caplog.records)
    assert any("disabled" in record.message.lower() for record in caplog.records)


@pytest.mark.django_db
def test_kill_switch_middleware_logs_errors(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test kill_switch_middleware logs errors when settings check fails"""
    import logging

    caplog.set_level(logging.ERROR)

    request = request_factory.post("/api/v1/contact/")

    with patch(
        "core.models.LandingPageSettings.objects.first",
        side_effect=DatabaseError("Database error"),
    ):
        kill_switch_middleware.process_request(request)

    assert any("database error" in record.message.lower() for record in caplog.records)
    assert any("settings" in record.message.lower() for record in caplog.records)
