from __future__ import annotations

from abc import ABCMeta, abstractmethod

from django.db.models.base import ModelBase

from common.types import ImageProcessingOperation


class DjangoModelABCMeta(ModelBase, ABCMeta):
    """Combine Django's model metaclass with ``ABCMeta`` for abstract model mixins."""


class ImageProcessingModelMixin(metaclass=DjangoModelABCMeta):
    """Runtime contract for Django models using the shared processing workflow.

    Concrete models inherit this mixin and implement the methods required by the
    shared workflow. The mixin intentionally keeps the contract small:

    - describe which operations should run

    The typing mirror of this contract lives in ``common.protocols`` so tasks
    and helpers can stay loosely coupled to concrete model classes.
    """

    @abstractmethod
    def get_image_processing_operations(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageProcessingOperation]:
        """Return the operations the shared workflow should execute.

        Args:
            changed_field_names: Optional list of logical image field names that
                changed on the model and therefore need processing.

        Returns:
            A list of ``ImageProcessingOperation`` objects describing the source
            image, target fields, conversion spec, and any optional thumbnail or
            original-file handling for this model instance.
        """
        raise NotImplementedError
