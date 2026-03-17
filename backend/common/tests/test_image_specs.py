from django.conf import settings
from django.test import SimpleTestCase

from common.utils.image import ImageSpec


class ImageSpecsConfigTest(SimpleTestCase):
    """Test that IMAGE_OPTIMIZATION_SPECS is correctly configured in settings."""

    def test_settings_has_image_specs(self):
        """Verify that IMAGE_OPTIMIZATION_SPECS exists and has expected keys."""
        # This justifies removing getattr() - we enforce it exists here.
        specs = settings.IMAGE_OPTIMIZATION_SPECS
        self.assertIsInstance(specs, dict)
        self.assertIn("AVATAR", specs)
        self.assertIn("PORTRAIT", specs)
        self.assertIn("LANDSCAPE", specs)
        self.assertIn("DEFAULT", specs)

    def test_specs_are_valid_instances(self):
        """Verify that each spec is an ImageSpec instance with valid values."""
        for key, spec in settings.IMAGE_OPTIMIZATION_SPECS.items():
            with self.subTest(key=key):
                self.assertIsInstance(spec, ImageSpec)
                self.assertGreater(spec.dimension, 0, f"Dimension for {key} must be > 0")
                self.assertGreaterEqual(spec.quality, 1, f"Quality for {key} must be >= 1")
                self.assertLessEqual(spec.quality, 100, f"Quality for {key} must be <= 100")
