import json
import logging

import pytest

from django.conf import settings
from django.core.cache import cache
from django.test import Client, override_settings
from django.urls import reverse

CSP_REPORT_PATH = "/csp-report/"
MAX_REPORT_SIZE = 16_384


def _valid_payload(**report_fields):
    report = {
        "violated-directive": "style-src-attr",
        "blocked-uri": "inline",
        "document-uri": "https://admin.example/admin/",
    }
    report.update(report_fields)
    return {"csp-report": report}


def _post_report(client, payload, content_type="application/csp-report", **extra):
    return client.post(
        CSP_REPORT_PATH,
        data=json.dumps(payload),
        content_type=content_type,
        **extra,
    )


def test_admin_login_uses_report_only_policy_without_changing_other_headers():
    client = Client()

    admin_response = client.get(reverse("admin:login"), secure=True)

    assert admin_response.status_code == 200
    policy = admin_response["Content-Security-Policy-Report-Only"]
    assert "default-src 'self'" in policy
    assert "style-src 'self'" in policy
    assert "img-src 'self' data: blob:" in policy
    assert "font-src 'self' data:" in policy
    assert "worker-src 'self' blob:" in policy
    assert "object-src 'none'" in policy
    assert "frame-src 'none'" in policy
    assert "report-uri /csp-report/" in policy
    assert "unsafe-inline" not in policy
    assert "Content-Security-Policy" not in admin_response
    assert admin_response["X-Frame-Options"] == "DENY"

    health_response = client.get(reverse("health"), secure=True)
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "healthy"}
    assert health_response["X-Frame-Options"] == "DENY"


@pytest.mark.parametrize("content_type", ["application/csp-report", "application/json"])
def test_anonymous_browser_report_is_accepted_without_csrf(content_type):
    client = Client(enforce_csrf_checks=True)

    response = _post_report(client, _valid_payload(), content_type)

    assert response.status_code == 204
    assert response.content == b""


def test_report_get_is_not_allowed():
    response = Client().get(CSP_REPORT_PATH)

    assert response.status_code == 405


@pytest.mark.parametrize(
    "body",
    [
        b"{not json",
        b"[]",
        b'{"csp-report": []}',
        b'{"csp-report": {"violated-directive": []}}',
        b'{"csp-report": {"violated-directive": "style-src", "blocked-uri": 1}}',
        b'{"csp-report": {"violated-directive": "script-src; report-uri https://evil/"}}',
        b'{"csp-report": {"violated-directive": ""}}',
    ],
)
def test_invalid_report_shapes_return_bad_request(body):
    response = Client().post(
        CSP_REPORT_PATH,
        data=body,
        content_type="application/csp-report",
    )

    assert response.status_code == 400


def test_unsupported_report_content_type_returns_unsupported_media_type():
    response = Client().post(
        CSP_REPORT_PATH,
        data="{}",
        content_type="text/plain",
    )

    assert response.status_code == 415


def test_report_body_limit_checks_actual_body_and_valid_content_length():
    client = Client()
    oversized_body = b" " * (MAX_REPORT_SIZE + 1)

    actual_size_response = client.post(
        CSP_REPORT_PATH,
        data=oversized_body,
        content_type="application/csp-report",
    )
    declared_size_response = client.post(
        CSP_REPORT_PATH,
        data=json.dumps(_valid_payload()),
        content_type="application/csp-report",
        CONTENT_LENGTH=str(MAX_REPORT_SIZE + 1),
    )

    assert actual_size_response.status_code == 413
    assert declared_size_response.status_code == 413


def test_report_log_contains_only_sanitized_bounded_violation_fields(caplog):
    payload = _valid_payload(
        **{
            "violated-directive": "style-src-attr\r\ninjected",
            "blocked-uri": "https://user:password@cdn.example/assets/app.css?token=secret#frag",
            "document-uri": "https://admin.example/admin/?session=secret#frag",
            "source-file": "https://admin.example/source?source-secret=secret",
            "script-sample": "private script sample secret",
        }
    )

    with caplog.at_level(logging.INFO, logger="common.csp_reports"):
        response = _post_report(Client(), payload)

    assert response.status_code == 204
    [record] = [
        record for record in caplog.records if getattr(record, "event", None) == "csp_violation"
    ]
    assert record.violated_directive == "style-src-attr"
    assert record.blocked_uri == "https://cdn.example"
    assert record.document_uri == "https://admin.example/admin/"
    assert "secret" not in caplog.text
    assert "source_file" not in record.__dict__
    assert "script_sample" not in record.__dict__
    assert "\r" not in record.violated_directive
    assert "\n" not in record.violated_directive


def test_report_log_only_includes_directive_name(caplog):
    payload = _valid_payload(
        **{
            "violated-directive": "script-src 'nonce-private' https://host/path?token=secret",
        }
    )

    with caplog.at_level(logging.INFO, logger="common.csp_reports"):
        response = _post_report(Client(), payload)

    assert response.status_code == 204
    [record] = [
        record for record in caplog.records if getattr(record, "event", None) == "csp_violation"
    ]
    assert record.violated_directive == "script-src"
    assert "nonce-private" not in caplog.text
    assert "token=secret" not in caplog.text


def test_effective_directive_takes_precedence_over_violated_directive(caplog):
    payload = _valid_payload(
        **{
            "effective-directive": "script-src-elem",
            "violated-directive": "default-src 'self' https://source.example",
        }
    )

    with caplog.at_level(logging.INFO, logger="common.csp_reports"):
        response = _post_report(Client(), payload)

    assert response.status_code == 204
    [record] = [
        record for record in caplog.records if getattr(record, "event", None) == "csp_violation"
    ]
    assert record.violated_directive == "script-src-elem"
    assert "https://source.example" not in caplog.text


def test_report_urls_are_parsed_before_sanitized_values_are_truncated(caplog):
    userinfo = "usersecret-" * 200
    url = f"https://{userinfo}@cdn.example/assets/admin.css?token=query-secret#fragment-secret"
    payload = _valid_payload(**{"blocked-uri": url, "document-uri": url})

    with caplog.at_level(logging.INFO, logger="common.csp_reports"):
        response = _post_report(Client(), payload)

    assert response.status_code == 204
    [record] = [
        record for record in caplog.records if getattr(record, "event", None) == "csp_violation"
    ]
    assert record.blocked_uri == "https://cdn.example"
    assert record.document_uri == "https://cdn.example/assets/admin.css"
    assert "usersecret" not in caplog.text
    assert "query-secret" not in caplog.text
    assert "fragment-secret" not in caplog.text


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "csp-report-throttle-tests",
        }
    }
)
def test_report_endpoint_is_limited_to_thirty_requests_per_minute():
    cache.clear()
    client = Client()
    payload = _valid_payload()

    for _ in range(30):
        assert _post_report(client, payload).status_code == 204

    assert _post_report(client, payload).status_code == 429
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["csp_report"] == "30/min"
    cache.clear()
