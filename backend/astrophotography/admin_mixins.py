from typing import Any
from urllib.parse import urlencode

from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from common.utils.signing import generate_signed_url_params
from core.models import ImageVariant


class SecureAdminSidebarPreviewMixin:
    """
    Mixin for ModelAdmin to inject secure signed URLs for sidebar previews.
    Handles the canonical source field and thumbnail by default.
    """

    secure_preview_fields = ["original", "thumbnail"]
    secure_preview_url_name = "admin-generic-secure-media"  # Default to generic view

    def _add_secure_sidebar_previews(self, obj: Model, context: dict[str, Any]) -> None:
        """Centralized logic to generate signed URLs and update context."""
        for field_name in self.secure_preview_fields:
            field = getattr(obj, field_name, None)
            if not field:
                continue

            # Build URL for the specific field
            url = reverse(
                self.secure_preview_url_name,
                kwargs=(
                    {
                        "app_label": obj._meta.app_label,
                        "model_name": obj._meta.model_name,
                        "pk": str(obj.pk),
                        "field_name": field_name,
                    }
                    if self.secure_preview_url_name == "admin-generic-secure-media"
                    else {"pk": str(obj.pk), "field_name": field_name}
                ),
            )

            # Generate signature
            sig_id = (
                f"admin_media_{obj._meta.app_label}_{obj._meta.model_name}_{obj.pk}_{field_name}"
            )
            params = generate_signed_url_params(sig_id, 3600)
            signed_url = f"{url}?{urlencode(params)}"

            # Map to template context names
            if field_name == "original":
                context["sidebar_image_url"] = signed_url
            elif field_name == "thumbnail":
                context["sidebar_thumbnail_url"] = signed_url

    model: type[Model]

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        """Inject secure previews into context if an object is being edited."""
        extra_context = extra_context or {}
        if object_id:
            obj: Model = get_object_or_404(self.model, pk=object_id)
            self._add_secure_sidebar_previews(obj, extra_context)

        return super().changeform_view(  # type: ignore[misc, no-any-return]
            request, object_id, form_url, extra_context
        )


class IgnoreImageVariantCascadeDeletePermissionMixin:
    """Allow deleting image owners without separately granting ImageVariant deletion.

    ImageVariant rows are generated implementation detail for image-owning models.
    When deleting an AstroImage or background image from admin, Django's delete
    confirmation collects cascade targets and would otherwise require explicit
    delete permission for the related ImageVariant model too. This mixin keeps
    the cascade visible in the confirmation tree while removing that derived-model
    permission from the blocking set.
    """

    def get_deleted_objects(self, objs, request):
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = super().get_deleted_objects(  # type: ignore[misc]
            objs, request
        )
        if perms_needed:
            perms_needed.discard(str(ImageVariant._meta.verbose_name))
            perms_needed.discard(str(ImageVariant._meta.verbose_name_plural))
        return deleted_objects, model_count, perms_needed, protected
