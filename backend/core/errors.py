from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

# Centralized template path
ERROR_TEMPLATE = "core/errors/error_secure.html"


def _render_themed_error(
    request: HttpRequest, status_code: int, status_text: str, message: str
) -> HttpResponse:
    """
    Internal source of truth for rendering themed HTML error responses.
    Centralizing this preserves DRY and makes it easy to add new error types.
    """
    return render(
        request,
        ERROR_TEMPLATE,
        {
            "status_code": status_code,
            "status_text": status_text,
            "message": message,
            "site_domain": settings.SITE_DOMAIN,
        },
        status=status_code,
    )


def render_404_error(request: HttpRequest, message: str = "File not found.") -> HttpResponse:
    """Professional 404 handler."""
    return _render_themed_error(request, 404, "Not Found", message)


def render_403_error(request: HttpRequest, message: str = "Access denied.") -> HttpResponse:
    """Professional 403 handler."""
    return _render_themed_error(request, 403, "Forbidden", message)


def render_500_error(request: HttpRequest, message: str = "Internal server error.") -> HttpResponse:
    """Example of how easily we can now extend to other codes (OCP)."""
    return _render_themed_error(request, 500, "Server Error", message)
