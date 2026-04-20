from typing import Any

import pytest
from pytest_mock import MockerFixture

from django.core.files.base import ContentFile
from django.core.management import call_command

from astrophotography.tests.factories import AstroImageFactory
from users.models import User
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestConvertImagesToWebpCommand:
    def test_command_converts_images(self, mocker: MockerFixture) -> None:
        """Test that the command iterates correctly and calls conversion."""
        # Setup: Mock conversion result
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_call_command = mocker.patch(
            "core.management.commands.convert_images_to_webp.call_command"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")
        mocker.patch("core.models.process_image_task.delay_on_commit")

        fake_content = ContentFile(b"fake webp content", name="test.webp")
        mock_convert_to_webp.return_value = ("test.jpg", fake_content)
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        # Create objects with actual image content from factory
        astro_img = AstroImageFactory()
        # Ensure User exists and has some images
        user = User.get_user()
        if not user:
            user = UserFactory.create_superuser()

        if not user.avatar:
            user.avatar.save("avatar.jpg", ContentFile(b"fake jpeg"), save=True)

        if user.avatar and user.avatar.name.endswith(".webp"):
            user.avatar.save("avatar.jpg", ContentFile(b"fake jpeg"), save=True)

        # Run command
        call_command("convert_images_to_webp")

        # Verify AstroImage was converted
        astro_img.refresh_from_db()
        assert astro_img.path.name.endswith(".jpg")
        assert astro_img.original is not None
        assert astro_img.original_webp is not None
        assert astro_img.original_webp.name.endswith(".webp")

        # Verify User avatar was converted
        user.refresh_from_db()
        assert user.avatar.name.endswith(".jpg")
        assert user.avatar_webp is not None

        # Verify cache clearing was called
        mock_call_command.assert_any_call("clear_cache")

    def test_command_dry_run_no_changes(self, mocker: MockerFixture) -> None:
        """Test that --dry-run does not modify the database."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_convert_to_webp.return_value = (
            "test.jpg",
            ContentFile(b"fake webp content", name="test.webp"),
        )
        # Prevent automatic task execution during factory creation for this test
        mocker.patch("core.models.process_image_task.delay_on_commit")
        astro_img = AstroImageFactory()
        path_before = astro_img.path.name

        call_command("convert_images_to_webp", dry_run=True)

        astro_img.refresh_from_db()
        assert astro_img.path.name == path_before
        assert not astro_img.original_webp

    def test_command_force_reconversion(self, mocker: MockerFixture) -> None:
        """Test that --force re-converts already converted images."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        # 1. First conversion
        mock_convert_to_webp.return_value = (
            "test.jpg",
            ContentFile(b"fake webp content", name="test.webp"),
        )
        mocker.patch("core.models.process_image_task.delay_on_commit")
        astro_img = AstroImageFactory()
        call_command("convert_images_to_webp")

        astro_img.refresh_from_db()
        assert astro_img.path.name.endswith(".jpg")
        assert astro_img.original == "test.jpg"
        assert astro_img.original_webp.name.endswith(".webp")

        # 2. Second run without force - should skip
        mock_convert_to_webp.reset_mock()
        call_command("convert_images_to_webp")
        mock_convert_to_webp.assert_not_called()

        # 3. Third run with force - should reconvert from the canonical source upload
        call_command("convert_images_to_webp", force=True)
        assert mock_convert_to_webp.called
        call_args: Any = mock_convert_to_webp.call_args[0][0]
        assert call_args.name == astro_img.original.name

    def test_command_object_id_limits_conversion_to_single_object(
        self, mocker: MockerFixture
    ) -> None:
        """Test that --object-id only converts the requested BaseImage record."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_call_command = mocker.patch(
            "core.management.commands.convert_images_to_webp.call_command"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")
        mocker.patch("core.models.process_image_task.delay_on_commit")

        fake_content = ContentFile(b"fake webp content", name="test.webp")
        mock_convert_to_webp.return_value = ("test.jpg", fake_content)
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        target = AstroImageFactory()
        other = AstroImageFactory()

        other_path_before = other.path.name

        call_command("convert_images_to_webp", object_id=str(target.pk))

        target.refresh_from_db()
        other.refresh_from_db()

        assert target.path.name.endswith(".jpg")
        assert target.original_webp is not None
        assert other.path.name == other_path_before
        assert other.original_webp in (None, "")
        assert target.original_webp.name.endswith(".webp")
        mock_call_command.assert_any_call("clear_cache")

    def test_command_object_ids_limits_conversion_to_requested_objects(
        self, mocker: MockerFixture
    ) -> None:
        """Test that --object-ids only converts the requested BaseImage records."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_call_command = mocker.patch(
            "core.management.commands.convert_images_to_webp.call_command"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")
        mocker.patch("core.models.process_image_task.delay_on_commit")

        fake_content = ContentFile(b"fake webp content", name="test.webp")
        mock_convert_to_webp.return_value = ("test.jpg", fake_content)
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        first = AstroImageFactory()
        second = AstroImageFactory()
        third = AstroImageFactory()

        third_path_before = third.path.name

        call_command(
            "convert_images_to_webp",
            object_ids=[str(first.pk), str(second.pk)],
        )

        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()

        assert first.path.name.endswith(".jpg")
        assert first.original_webp is not None
        assert second.path.name.endswith(".jpg")
        assert second.original_webp is not None
        assert third.path.name == third_path_before
        assert third.original_webp in (None, "")
        mock_call_command.assert_any_call("clear_cache")

    def test_command_dimension_percentage_is_passed_to_converter(
        self, mocker: MockerFixture
    ) -> None:
        """Command-level dimension percentage should override the converter input."""
        mock_convert_to_webp = mocker.patch(
            "core.management.commands.convert_images_to_webp.convert_to_webp"
        )
        mock_make_thumb = mocker.patch("astrophotography.models.AstroImage.make_thumbnail")
        mock_call_command = mocker.patch(
            "core.management.commands.convert_images_to_webp.call_command"
        )

        fake_content = ContentFile(b"fake webp content", name="test.webp")
        mock_convert_to_webp.return_value = ("test.jpg", fake_content)
        mock_make_thumb.return_value = ContentFile(b"thumb", name="thumb.webp")

        mocker.patch("core.models.process_image_task.delay_on_commit")
        target = AstroImageFactory()

        call_command(
            "convert_images_to_webp",
            object_id=str(target.pk),
            dimension_percentage=50,
        )

        assert mock_convert_to_webp.called
        assert mock_convert_to_webp.call_args.kwargs["dimension_percentage"] == 50
        mock_call_command.assert_any_call("clear_cache")
