# backend/astrophotography/tests/test_models.py
import pytest

from astrophotography.models import AstroImage
from astrophotography.tests.factories import AstroImageFactory, BackgroundMainPageFactory


@pytest.mark.django_db
class TestAstroImageModel:
    def test_string_representation(self):
        """Test AstroImage string representation uses the name field"""
        image = AstroImageFactory(name="Test Nebula")
        assert str(image) == "Test Nebula"

    def test_default_ordering(self):
        """Test default ordering is by created_at descending (from BaseImage)"""
        image1 = AstroImageFactory(name="Image 1")
        image2 = AstroImageFactory(name="Image 2")
        # Verify ordering (newest first)
        qs = AstroImage.objects.all()
        assert qs[0] == image2
        assert qs[1] == image1


@pytest.mark.django_db
class TestBackgroundMainPageModel:
    def test_string_representation(self):
        """Test BackgroundMainPage string representation"""
        bg = BackgroundMainPageFactory()
        assert str(bg) == f"BackgroundMainPage {bg.pk}"
