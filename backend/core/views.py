"""
Shared views and utility endpoints for the core application.
"""

import logging
from typing import Any, Optional, cast

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from common.utils.logging import sanitize_for_logging
from common.utils.signing import validate_signed_url
from core.errors import render_403_error, render_404_error
from core.models import LandingPageSettings
from core.serializers import LandingPageSettingsSerializer

logger = logging.getLogger(__name__)


class SettingsView(generics.RetrieveAPIView):
    """
    Endpoint to fetch global application settings.
    - 'features': Boolean flags for enabled system modules.
    - 'meteors': Configuration for the shooting stars effect.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LandingPageSettingsSerializer
    queryset = LandingPageSettings.objects.all()

    def get_object(self) -> LandingPageSettings:
        """
        Returns the singleton LandingPageSettings instance or raises 404.
        """
        obj = self.get_queryset().last()
        if not obj:
            raise Http404("Landing Page Settings not initialized.")
        return cast(LandingPageSettings, obj)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
@throttle_classes([])
def health_check_view(request: Request) -> Response:
    """
    Simple health check endpoint returning 200 OK.
    """
    return Response({"status": "healthy"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def root_view(request: Request) -> Any:
    """
    Root view for all domains.
    - ADMIN_DOMAIN: Redirects to /admin/
    - Others: Redirects to SITE_DOMAIN (FE main page)
    """
    from django.conf import settings
    from django.shortcuts import redirect

    host = request.get_host().split(":")[0]  # Remove port if present
    if host == settings.ADMIN_DOMAIN:
        return redirect("admin:index")

    return redirect(f"https://{settings.SITE_DOMAIN}/")


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def v1_root_view(request: Request) -> Any:
    """
    API v1 root greetings page with a pretty template.
    """
    return render(request, "core/api_v1_greetings.html")


@api_view(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
@permission_classes([permissions.AllowAny])
def api_404_view(request: Request, *args: Any, **kwargs: Any) -> Response:
    """
    Catch-all view for unmatched API endpoints.
    Ensures 404 Not Found is returned as JSON instead of falling through to admin.
    """
    return Response(
        {"detail": f"Endpoint '{request.path}' not found."},
        status=status.HTTP_404_NOT_FOUND,
    )


class SecureMediaView(APIView):
    """
    Base view to carefully serve secure, internal media via Nginx X-Accel-Redirect.
    Extending classes MUST implement get_object(), get_file_path(), and get_signature_id().
    """

    permission_classes = [permissions.AllowAny]
    content_disposition: str = "inline"

    def get_object(self) -> Model:
        raise NotImplementedError("Subclasses must implement get_object")

    def get_file_path(self, obj: Model) -> str:
        raise NotImplementedError("Subclasses must implement get_file_path")

    def get_signature_id(self) -> str:
        """Return the unique ID string used to validate the signature."""
        return str(self.kwargs.get("slug", "") or self.kwargs.get("pk", ""))

    def _validate_signature(self, request: Request, identifier: str) -> Optional[HttpResponse]:
        """
        Validates the request signature and returns an error response if invalid,
        or None if valid.
        """
        safe_identifier: str = sanitize_for_logging(identifier)
        signature: Optional[str] = request.query_params.get("s")
        expiration: Optional[str] = request.query_params.get("e")

        safe_signature: str = sanitize_for_logging(signature) if signature else "None"
        safe_expiration: str = sanitize_for_logging(expiration) if expiration else "None"

        if not signature or not expiration:
            logger.warning(
                f"Missing signature params for secure media. ID: {safe_identifier}, "
                f"S: {bool(signature)}, E: {bool(expiration)}"
            )
            return render_403_error(request, "Missing signature parameters.")

        if not validate_signed_url(identifier, signature, expiration):
            logger.warning(
                f"Invalid or expired signature for secure media. ID: {safe_identifier}, "
                f"S: {safe_signature[:8]}..., E: {safe_expiration}"
            )
            return render_403_error(
                request, "The link has expired or is invalid. Please refresh the page."
            )

        return None

    def get(self, request: Request, *args: Any, **kwargs: Any) -> HttpResponse:
        safe_path = sanitize_for_logging(request.get_full_path())
        logger.info(f"SecureMediaView.get() hit: {safe_path}")
        identifier = self.get_signature_id()

        validation_error_response = self._validate_signature(request, identifier)
        if validation_error_response:
            return validation_error_response

        # Get the object exactly how the subclass wants
        try:
            obj: Model = self.get_object()
            file_path: str = self.get_file_path(obj)
        except (Http404, ObjectDoesNotExist):
            return render_404_error(request)

        if not file_path:
            safe_identifier: str = sanitize_for_logging(identifier)
            logger.error(
                f"Object record found but file path missing/empty for ID: {safe_identifier}"
            )
            return render_404_error(request)

        filename = file_path.split("/")[-1]
        response = HttpResponse()
        # This path must match the 'location /protected_media/' block in nginx.conf
        redirect_uri: str = f"/protected_media/{file_path}"
        response["X-Accel-Redirect"] = redirect_uri
        response["Content-Type"] = ""  # Let Nginx determine the content type
        response["Content-Disposition"] = f'{self.content_disposition}; filename="{filename}"'
        logger.info(
            f"Serving secure media via Nginx redirect: {redirect_uri} "
            f"as {filename} ({self.content_disposition})"
        )
        return response


class GenericAdminSecureMediaView(SecureMediaView):
    """
    Universal internal media serving for Admin.
    Handles any model/field via: /admin/media/<app>/<model>/<pk>/<field>/
    Requires: Staff status + Valid signature.
    """

    def get(self, request, *args, **kwargs):
        if not getattr(request.user, "is_staff", False):
            return render_404_error(request)

        try:
            # Call the specific media view's get()
            return super().get(request, *args, **kwargs)
        except Http404:
            return render_404_error(request)

    def get_object(self) -> Model:
        from django.apps import apps

        app_label = self.kwargs.get("app_label")
        model_name = self.kwargs.get("model_name")
        pk = self.kwargs.get("pk")

        model_class = apps.get_model(app_label, model_name)
        return cast(Model, get_object_or_404(model_class, pk=pk))

    def get_file_path(self, obj: Model) -> str:
        field_name = self.kwargs.get("field_name")
        field = getattr(obj, field_name, None)

        if not field or not hasattr(field, "name") or not field.name:
            raise Http404(f"Field '{field_name}' not found or empty on {obj._meta.model_name}")

        return str(field.name)

    def get_signature_id(self) -> str:
        # Signature is bound to the specific resource path
        app = self.kwargs.get("app_label")
        model = self.kwargs.get("model_name")
        pk = self.kwargs.get("pk")
        field = self.kwargs.get("field_name")
        return f"admin_media_{app}_{model}_{pk}_{field}"
