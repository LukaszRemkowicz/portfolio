from __future__ import annotations

from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.background import submit
from common.types import ImageVariantSource, ImageVariantSpec, ViewportWidths
from core.mixins import ImageVariantModelMixin
from core.models import ImageVariant
from core.tasks import process_image_task
from translation.mixins import AutomatedTranslationModelMixin


class Project(ImageVariantModelMixin, AutomatedTranslationModelMixin, TranslatableModel):
    """A programming project shown in the public Projects section."""

    image_variant_specs = (
        ImageVariantSpec(
            role="original_format",
            viewport_widths=ViewportWidths.fixed(1600),
            quality=90,
            label="Project cover original-format display candidate",
        ),
        ImageVariantSpec(
            role="thumbnail",
            viewport_widths=ViewportWidths.fixed(800),
            quality=85,
            label="Project cover thumbnail",
        ),
    )

    translation_service_method = "translate_project"
    translation_trigger_fields = ["name", "description"]

    image_tracker = FieldTracker(fields=["image", "image_cropped"])

    technologies = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Technologies"),
        help_text=_("Comma-separated list, e.g. Python, Django, React."),
    )
    github_url = models.URLField(blank=True, verbose_name=_("GitHub URL"))
    live_url = models.URLField(blank=True, verbose_name=_("Live URL"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    pricing = models.CharField(
        max_length=8,
        choices=[("", _("No label")), ("free", _("Free")), ("paid", _("Paid"))],
        blank=True,
        default="",
        verbose_name=_("Pricing"),
        help_text=_("Price label shown on the project card; the frontend renders it."),
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Price"),
        help_text=_("Required when pricing is Paid; ignored otherwise."),
    )
    currency = models.CharField(
        max_length=3,
        default="PLN",
        verbose_name=_("Currency"),
        help_text=_("ISO 4217 currency code, e.g. USD, EUR, PLN."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    image = models.ImageField(
        upload_to="programming/projects/",
        verbose_name=_("Cover Source"),
        help_text=_("The source screenshot used for the project cover."),
    )
    image_cropped = models.ImageField(
        upload_to="programming/projects/",
        null=True,
        blank=True,
        verbose_name=_("Cover Cropped"),
        help_text=_("Cropped cover image managed by the admin image cropper."),
    )
    variants = GenericRelation(
        ImageVariant,
        content_type_field="content_type",
        object_id_field="object_id",
    )

    translations = TranslatedFields(
        name=models.CharField(max_length=255, verbose_name=_("Name")),
        description=CKEditor5Field(
            blank=True,
            verbose_name=_("Description"),
            config_name="default",
        ),
    )

    objects = TranslatableManager()  # type: ignore[django-manager-missing,misc]

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.safe_translation_getter("name", any_language=True) or f"Project {self.pk}"

    def clean(self) -> None:
        super().clean()
        if self.pricing == "paid" and (self.price is None or self.price <= 0):
            raise ValidationError({"price": _("A price greater than 0 is required when Paid.")})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Reset the crop on a new source, schedule image processing, trigger translations."""
        if self.pricing != "paid" and self.price is not None:
            self.price = None
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"price"}
        source_changed: bool = self.image_tracker.has_changed("image")
        cropped_changed: bool = self.image_tracker.has_changed("image_cropped")
        update_fields = kwargs.get("update_fields")
        image_update_fields = {"image", "image_cropped"}
        should_process_images = bool(source_changed or cropped_changed) and (
            update_fields is None or bool(image_update_fields.intersection(set(update_fields)))
        )

        if source_changed and not cropped_changed:
            self.image_cropped = None
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"image_cropped"}

        super().save(*args, **kwargs)

        if should_process_images:
            submit(
                process_image_task,
                self._meta.app_label,
                self._meta.model_name,
                self.pk,
                sorted(image_update_fields),
            )

        if not update_fields or any(
            field in update_fields for field in self.translation_trigger_fields
        ):
            self.trigger_translations()

    def get_image_variant_sources(
        self, _changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]:
        source_image = self.image_cropped or self.image
        return [
            ImageVariantSource(
                field_name="image",
                source_image=source_image,
                upload_dir="programming/projects",
            )
        ]
