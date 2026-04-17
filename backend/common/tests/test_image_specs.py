from django.conf import settings
from django.test import SimpleTestCase

from common.types import ImageSpec


class ImageSpecsConfigTest(SimpleTestCase):
    """Test that IMAGE_OPTIMIZATION_SPECS is correctly configured in settings."""

    def test_settings_has_image_specs(self):
        """Verify that IMAGE_OPTIMIZATION_SPECS exists and has expected keys."""
        # This justifies removing getattr() - we enforce it exists here.
        specs = settings.IMAGE_OPTIMIZATION_SPECS
        assert isinstance(specs, dict)
        assert "AVATAR" in specs
        assert "PORTRAIT" in specs
        assert "LANDSCAPE" in specs
        assert "DEFAULT" in specs

    def test_specs_are_valid_instances(self):
        """Verify that each spec is an ImageSpec instance with valid values."""
        for key, spec in settings.IMAGE_OPTIMIZATION_SPECS.items():
            with self.subTest(key=key):
                assert isinstance(spec, ImageSpec)
                assert spec.dimension > 0, f"Dimension for {key} must be > 0"
                assert spec.quality >= 1, f"Quality for {key} must be >= 1"
                assert spec.quality <= 100, f"Quality for {key} must be <= 100"
