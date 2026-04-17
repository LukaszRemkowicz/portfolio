from __future__ import annotations

from dataclasses import dataclass

from django.core.files.base import ContentFile

from common.image_processing import process_image_operations
from common.tests.image_helpers import _jpeg_field, _png_field
from common.types import ImageProcessingOperation, ImageSpec


@dataclass
class _ConcreteField:
    name: str


class _Meta:
    def __init__(self, field_names: list[str]) -> None:
        self.concrete_fields = [_ConcreteField(name) for name in field_names]


class _SavedFieldFile:
    def __init__(self) -> None:
        self.saved_name: str | None = None
        self.saved_content: ContentFile | None = None
        self.saved_with_flag: bool | None = None

    def save(self, name: str, content: ContentFile, save: bool = False) -> None:
        self.saved_name = name
        self.saved_content = content
        self.saved_with_flag = save


class _DummyImageModel:
    def __init__(self, *, with_updated_at: bool = True) -> None:
        field_names = ["image_webp", "thumbnail"]
        if with_updated_at:
            field_names.append("updated_at")
            self.updated_at = object()
        self._meta = _Meta(field_names)
        self.image_webp = _SavedFieldFile()
        self.thumbnail = _SavedFieldFile()
        self.original_image: str | None = None
        self.save_calls: list[list[str]] = []
        self.operations: list[ImageProcessingOperation] = []

    def get_image_processing_operations(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageProcessingOperation]:
        return self.operations

    def save(self, *args: object, **kwargs: object) -> None:
        update_fields = kwargs.get("update_fields")
        self.save_calls.append(list(update_fields) if update_fields else [])


class TestProcessImageOperations:
    def test_converts_and_saves_webp_original_and_thumbnail(self, mocker) -> None:
        instance = _DummyImageModel()
        source_image = _jpeg_field("uploads/source.jpg")
        thumbnail_content = ContentFile(b"thumb-bytes", name="thumb.webp")
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=source_image,
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
                original_field_name="original_image",
                thumbnail_field_name="thumbnail",
                thumbnail_generator=lambda _source: thumbnail_content,
            )
        ]
        mocker.patch(
            "common.image_processing.convert_to_webp",
            return_value=("uploads/source.jpg", ContentFile(b"webp-bytes", name="source.webp")),
        )

        updated_fields = process_image_operations(instance)

        assert updated_fields == ["image_webp", "original_image", "thumbnail"]
        assert instance.image_webp.saved_name == "source.webp"
        assert instance.original_image == "uploads/source.jpg"
        assert instance.thumbnail.saved_name == "thumb.webp"
        assert instance.save_calls == [["image_webp", "original_image", "thumbnail", "updated_at"]]

    def test_clears_target_field_when_source_missing(self) -> None:
        instance = _DummyImageModel()
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=None,
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
            )
        ]

        updated_fields = process_image_operations(instance)

        assert updated_fields == ["image_webp"]
        assert instance.image_webp is None
        assert instance.save_calls == [["image_webp", "updated_at"]]

    def test_reuses_existing_webp_source_without_conversion(self, mocker) -> None:
        instance = _DummyImageModel()
        source_image = _png_field("uploads/already.webp")
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=source_image,
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
            )
        ]
        convert_mock = mocker.patch("common.image_processing.convert_to_webp")

        updated_fields = process_image_operations(instance)

        assert updated_fields == ["image_webp"]
        assert instance.image_webp == "already.webp"
        assert instance.save_calls == [["image_webp", "updated_at"]]
        convert_mock.assert_not_called()

    def test_clears_field_when_conversion_fails_and_flag_is_enabled(self, mocker) -> None:
        instance = _DummyImageModel()
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=_jpeg_field("uploads/source.jpg"),
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
                clear_field_on_failed_conversion=True,
            )
        ]
        mocker.patch("common.image_processing.convert_to_webp", return_value=None)

        updated_fields = process_image_operations(instance)

        assert updated_fields == ["image_webp"]
        assert instance.image_webp is None
        assert instance.save_calls == [["image_webp", "updated_at"]]

    def test_does_not_append_updated_at_when_model_lacks_field(self, mocker) -> None:
        instance = _DummyImageModel(with_updated_at=False)
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=_jpeg_field("uploads/source.jpg"),
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
            )
        ]
        mocker.patch(
            "common.image_processing.convert_to_webp",
            return_value=("uploads/source.jpg", ContentFile(b"webp-bytes", name="source.webp")),
        )

        updated_fields = process_image_operations(instance)

        assert updated_fields == ["image_webp"]
        assert instance.save_calls == [["image_webp"]]

    def test_falls_back_to_generated_name_when_content_has_no_name(self, mocker) -> None:
        instance = _DummyImageModel()
        nameless_content = ContentFile(b"webp-bytes")
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=_jpeg_field("uploads/source.jpg"),
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
            )
        ]
        mocker.patch(
            "common.image_processing.convert_to_webp",
            return_value=("uploads/source.jpg", nameless_content),
        )

        process_image_operations(instance)

        assert instance.image_webp.saved_name == "image_webp.webp"

    def test_save_fields_unchanged_when_instance_has_no_meta(self, mocker) -> None:
        instance = _DummyImageModel(with_updated_at=False)
        del instance._meta
        instance.operations = [
            ImageProcessingOperation(
                field_name="image",
                source_image=_jpeg_field("uploads/source.jpg"),
                webp_field_name="image_webp",
                spec=ImageSpec(dimension=1200, quality=75),
            )
        ]
        mocker.patch(
            "common.image_processing.convert_to_webp",
            return_value=("uploads/source.jpg", ContentFile(b"webp-bytes", name="source.webp")),
        )

        process_image_operations(instance)

        assert instance.save_calls == [["image_webp"]]
