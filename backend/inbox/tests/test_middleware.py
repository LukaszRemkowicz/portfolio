import json
import logging

import pytest

from django.http import JsonResponse
from django.test import RequestFactory

from core.tests.factories import LandingPageSettingsFactory
from inbox.middleware import ContactFormKillSwitchMiddleware


@pytest.mark.django_db
def test_kill_switch_middleware_allows_post_when_enabled(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
) -> None:
    """Test kill_switch_middleware allows POST requests when form is enabled"""
    LandingPageSettingsFactory(contact_form_enabled=True)
    request = request_factory.post("/api/v1/contact/")
    response = kill_switch_middleware.process_request(request)

    assert response is None, "Middleware should allow request when enabled"


@pytest.mark.django_db
def test_kill_switch_middleware_blocks_post_when_disabled(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
) -> None:
    """Test kill_switch_middleware blocks POST requests when form is disabled"""
    LandingPageSettingsFactory(contact_form_enabled=False)

    request = request_factory.post("/api/v1/contact/")
    response = kill_switch_middleware.process_request(request)

    assert response is not None, "Middleware should block request when disabled"
    assert isinstance(response, JsonResponse), "Response should be JsonResponse"
    assert response.status_code == 400, "Should return HTTP 400 Bad Request"

    response_data = json.loads(response.content)
    assert "message" in response_data
    assert "disabled" in response_data["message"].lower()


@pytest.mark.django_db
def test_kill_switch_middleware_ignores_non_post_requests(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
) -> None:
    """Test kill_switch_middleware ignores GET, PUT, DELETE, etc. requests"""
    LandingPageSettingsFactory(
        contact_form_enabled=False
    )  # Disabled, but should still allow non-POST

    for method in ["GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        request = getattr(request_factory, method.lower())("/api/v1/contact/")
        response = kill_switch_middleware.process_request(request)
        assert response is None, f"Middleware should ignore {method} requests"


@pytest.mark.django_db
def test_kill_switch_middleware_only_checks_contact_endpoint(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
) -> None:
    """Test kill_switch_middleware only checks contact endpoint, ignores other paths"""
    LandingPageSettingsFactory(contact_form_enabled=False)

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
) -> None:
    """Test kill_switch_middleware only checks exact DRF router path with trailing slash"""
    LandingPageSettingsFactory(contact_form_enabled=False)

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
def test_kill_switch_middleware_logs_blocked_requests(
    kill_switch_middleware: ContactFormKillSwitchMiddleware,
    request_factory: RequestFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test kill_switch_middleware logs blocked requests"""
    caplog.set_level(logging.WARNING)

    LandingPageSettingsFactory(contact_form_enabled=False)

    request = request_factory.post("/api/v1/contact/")
    response = kill_switch_middleware.process_request(request)

    assert response is not None
    assert any("blocked" in record.message.lower() for record in caplog.records)
    assert any("disabled" in record.message.lower() for record in caplog.records)
