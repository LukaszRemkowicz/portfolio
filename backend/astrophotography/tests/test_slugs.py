from django.test import TestCase
from django.utils.text import slugify

from astrophotography.tests.factories import AstroImageFactory


class AstroImageSlugTest(TestCase):
    def test_slug_auto_generated(self):
        """Test that slug is automatically generated from name on creation"""
        name = "Nebula in Orion"
        # This will currently fail because 'slug' field doesn't exist yet
        try:
            image = AstroImageFactory(name=name, slug=None)
            self.assertTrue(bool(image.slug))
            self.assertEqual(image.slug, slugify(name))
        except TypeError:
            # Factory might fail if it tries to set 'slug' which doesn't exist,
            # or if we try to access it.
            # We expect failure here in TDD phase.
            self.fail("Failed to set/access 'slug' field - it likely does not exist yet.")

    def test_slug_uniqueness(self):
        """Test that slugs are unique even if names are identical"""
        name = "Same Name"
        image1 = AstroImageFactory(name=name)
        image2 = AstroImageFactory(name=name)

        self.assertNotEqual(image1.slug, image2.slug)
        self.assertTrue(slugify(name) in image1.slug)
        self.assertTrue(slugify(name) in image2.slug)

    def test_slug_custom_set(self):
        """Test that providing a custom slug is respected"""
        custom_slug = "my-custom-slug"
        image = AstroImageFactory(slug=custom_slug)
        self.assertEqual(image.slug, custom_slug)
