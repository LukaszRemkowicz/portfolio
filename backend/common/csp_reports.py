import json
import logging
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from django.http import HttpResponse

from common.throttling import TrustedAnonRateThrottle

logger = logging.getLogger(__name__)

_MAX_REPORT_SIZE = 16_384
_MAX_DIRECTIVE_LENGTH = 256
_MAX_URL_LENGTH = 2_048
_SUPPORTED_CONTENT_TYPES = {"application/csp-report", "application/json"}
_NON_URL_BLOCKED_VALUES = {"eval", "inline", "self", "wasm-eval"}
_DIRECTIVE_NAME = re.compile(r"[a-z][a-z0-9-]{0,63}")


class CspReportThrottle(TrustedAnonRateThrottle):
    scope = "csp_report"


def _clean_text(value: str, max_length: int) -> str:
    value = "".join(
        " " if ord(character) < 32 or ord(character) == 127 else character for character in value
    )
    return " ".join(value.split())[:max_length]


def _safe_report_url(value: str, *, origin_only: bool) -> str:
    value = _clean_text(value, _MAX_REPORT_SIZE)
    if not value:
        return ""

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return ""

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not hostname:
        if origin_only and value.casefold() in _NON_URL_BLOCKED_VALUES:
            return value.casefold()
        return f"{scheme}:" if scheme else ""

    hostname = hostname.lower()
    if any(character.isspace() for character in hostname):
        return ""
    if ":" in hostname:
        hostname = f"[{hostname}]"
    netloc = f"{hostname}:{port}" if port is not None else hostname
    if origin_only:
        return f"{scheme}://{netloc}"[:_MAX_URL_LENGTH]
    return urlunsplit((scheme, netloc, parsed.path, "", ""))[:_MAX_URL_LENGTH]


def _parse_report_body(body: bytes) -> dict[str, Any] | None:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError, UnicodeDecodeError:
        return None

    if not isinstance(payload, dict):
        return None
    report = payload.get("csp-report")
    return report if isinstance(report, dict) else None


def _validated_report_fields(report: dict[str, Any]) -> tuple[str, str, str] | None:
    for field in ("violated-directive", "effective-directive", "blocked-uri", "document-uri"):
        if field in report and not isinstance(report[field], str):
            return None

    directive_value = report.get("effective-directive") or report.get("violated-directive")
    if not isinstance(directive_value, str):
        return None
    directive_parts = _clean_text(directive_value, _MAX_DIRECTIVE_LENGTH).split(maxsplit=1)
    if not directive_parts:
        return None
    directive = directive_parts[0]
    if not _DIRECTIVE_NAME.fullmatch(directive):
        return None

    return directive, report.get("blocked-uri", ""), report.get("document-uri", "")


class CspReportView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CspReportThrottle]

    def post(self, request):
        content_type = request.META.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower()
        if content_type not in _SUPPORTED_CONTENT_TYPES:
            return HttpResponse(status=415)

        content_length = request.META.get("CONTENT_LENGTH", "")
        if content_length.isascii() and content_length.isdecimal():
            if int(content_length) > _MAX_REPORT_SIZE:
                return HttpResponse(status=413)

        body = request.body
        if len(body) > _MAX_REPORT_SIZE:
            return HttpResponse(status=413)

        report = _parse_report_body(body)
        if report is None:
            return HttpResponse(status=400)
        fields = _validated_report_fields(report)
        if fields is None:
            return HttpResponse(status=400)

        directive, blocked_uri, document_uri = fields
        logger.info(
            "Content Security Policy violation report received",
            extra={
                "event": "csp_violation",
                "violated_directive": directive,
                "blocked_uri": _safe_report_url(blocked_uri, origin_only=True),
                "document_uri": _safe_report_url(document_uri, origin_only=False),
            },
        )
        return HttpResponse(status=204)
