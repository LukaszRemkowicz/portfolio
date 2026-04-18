"""Shared runtime workflow for model-driven image processing.

This module contains the reusable implementation used by image-owning models
that expose the image-processing contract through:

- ``common.protocols.ImageProcessingCapable`` for typing
- ``common.mixins.ImageProcessingModelMixin`` for runtime inheritance

The core idea is:

1. a model describes one or more image-processing operations,
2. the shared workflow executes those operations,
3. the model remains responsible for persistence.

This keeps the task/service layer generic while allowing each model family to
define its own source-field selection and target fields.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from common.protocols import ImageProcessingCapable
from common.types import ImageProcessingOperation
from common.utils.image import convert_to_webp

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile

logger = logging.getLogger(__name__)


def process_image_operations(
    instance: ImageProcessingCapable, changed_field_names: list[str] | None = None
) -> list[str]:
    """Process all configured image operations for a model instance.

    This function is the shared runtime engine used by the common task layer.
    It asks the model for operations, executes each operation, and saves any
    updated derived fields directly on the model instance.

    Args:
        instance: A model implementing the shared image-processing contract.
        changed_field_names: Optional logical field names that limit processing
            to a subset of operations for the current save/task run.

    Returns:
        A de-duplicated list of model field names that were updated by the
        processing workflow and then persisted by the model.
    """
    operations = instance.get_image_processing_operations(changed_field_names)
    logger.info(
        "Starting shared image processing",
        extra={
            "model": type(instance).__name__,
            "changed_field_names": changed_field_names or [],
            "operation_count": len(operations),
        },
    )
    updated_fields: list[str] = []

    for operation in operations:
        updated_fields.extend(_process_image_operation(instance, operation))

    unique_updated_fields = list(dict.fromkeys(updated_fields))
    if unique_updated_fields:
        instance.save(update_fields=_build_save_update_fields(instance, unique_updated_fields))
        logger.info(
            "Finished shared image processing with updates",
            extra={"model": type(instance).__name__, "updated_fields": unique_updated_fields},
        )
    else:
        logger.info(
            "Finished shared image processing without updates",
            extra={"model": type(instance).__name__},
        )

    return unique_updated_fields


def _process_image_operation(
    instance: ImageProcessingCapable, operation: ImageProcessingOperation
) -> list[str]:
    """Execute one ``ImageProcessingOperation`` against the given model instance.

    The operation flow is:

    1. resolve whether a usable source image exists,
    2. either clear, reuse, or generate the WebP field,
    3. optionally persist the original-field reference,
    4. optionally generate the thumbnail field.

    The function mutates the in-memory model instance but does not save it. The
    caller is responsible for persistence after all operations are complete.
    """
    source_image = operation.source_image
    updated_fields: list[str] = []

    if not source_image:
        if operation.clear_field_on_missing_source:
            setattr(instance, operation.webp_field_name, None)
            updated_fields.append(operation.webp_field_name)
            logger.info(
                "Cleared derived image field because source is missing",
                extra={
                    "model": type(instance).__name__,
                    "field_name": operation.field_name,
                    "webp_field_name": operation.webp_field_name,
                },
            )
        return updated_fields

    source_name = str(getattr(source_image, "name", "") or "")
    if source_name.lower().endswith(".webp"):
        setattr(instance, operation.webp_field_name, source_name)
        updated_fields.append(operation.webp_field_name)
        logger.info(
            "Reused existing WebP source for derived image field",
            extra={
                "model": type(instance).__name__,
                "field_name": operation.field_name,
                "webp_field_name": operation.webp_field_name,
                "source_name": source_name,
            },
        )
    else:
        result = convert_to_webp(
            source_image,
            quality=operation.spec.quality,
            max_dimension=operation.spec.dimension,
            dimension_percentage=operation.spec.dimension_percentage,
        )

        if result:
            original_name, webp_content = result
            webp_field = _get_field_file(instance, operation.webp_field_name)
            webp_field.save(
                _get_content_name(webp_content, operation.webp_field_name),
                webp_content,
                save=False,
            )
            updated_fields.append(operation.webp_field_name)
            logger.info(
                "Converted image source to WebP",
                extra={
                    "model": type(instance).__name__,
                    "field_name": operation.field_name,
                    "webp_field_name": operation.webp_field_name,
                    "original_name": original_name,
                },
            )
            if operation.original_field_name:
                setattr(instance, operation.original_field_name, original_name)
                updated_fields.append(operation.original_field_name)
        elif operation.clear_field_on_failed_conversion:
            setattr(instance, operation.webp_field_name, None)
            updated_fields.append(operation.webp_field_name)
            logger.warning(
                "Conversion skipped or failed for %s on %s",
                operation.field_name,
                type(instance).__name__,
            )
        else:
            logger.warning(
                "Conversion skipped or failed for %s on %s",
                operation.field_name,
                type(instance).__name__,
            )

    if operation.thumbnail_field_name and operation.thumbnail_generator:
        thumbnail_source = operation.thumbnail_source_image or source_image
        if thumbnail_source:
            thumbnail_field = _get_field_file(instance, operation.thumbnail_field_name)
            thumbnail_content = operation.thumbnail_generator(thumbnail_source)
            thumbnail_field.save(
                _get_content_name(thumbnail_content, operation.thumbnail_field_name),
                thumbnail_content,
                save=False,
            )
            updated_fields.append(operation.thumbnail_field_name)
            logger.info(
                "Generated thumbnail during shared image processing",
                extra={
                    "model": type(instance).__name__,
                    "field_name": operation.field_name,
                    "thumbnail_field_name": operation.thumbnail_field_name,
                },
            )

    return updated_fields


def _get_field_file(instance: Any, field_name: str) -> FieldFile:
    """Return the file-like Django model field object for a field name."""
    return cast("FieldFile", getattr(instance, field_name))


def _get_content_name(content: Any, field_name: str) -> str:
    """Return a non-empty filename for content saved through a Django file field."""
    content_name = getattr(content, "name", None)
    if isinstance(content_name, str) and content_name:
        return content_name
    return f"{field_name}.webp"


def _build_save_update_fields(instance: Any, updated_fields: list[str]) -> list[str]:
    """Return update_fields extended with ``updated_at`` when the model defines it."""
    save_fields = list(updated_fields)
    model_meta = getattr(instance, "_meta", None)
    if model_meta is None:
        return save_fields

    concrete_field_names = {field.name for field in getattr(model_meta, "concrete_fields", ())}
    if "updated_at" in concrete_field_names and "updated_at" not in save_fields:
        save_fields.append("updated_at")

    return save_fields
