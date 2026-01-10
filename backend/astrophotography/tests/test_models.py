# backend/astrophotography/tests/test_models.py
import pytest

from astrophotography.models import AstroImage, BackgroundMainPage


@pytest.mark.django_db
class TestAstroImageModel:
    def test_string_representation(self):
        """Test AstroImage string representation uses the name field"""
        image = AstroImage.objects.create(
            capture_date="2023-01-01",
            location="Test Location",
            celestial_object="Deep Sky",
            path="test.jpg",
            name="Test Nebula",
        )
        assert str(image) == "Test Nebula"

    def test_default_ordering(self):
        """Test default ordering is by created_at descending (from BaseImage)"""
        image1 = AstroImage.objects.create(
            capture_date="2023-01-01",
            location="Loc1",
            celestial_object="Deep Sky",
            path="1.jpg",
            name="Image 1",
        )
        image2 = AstroImage.objects.create(
            capture_date="2023-01-02",
            location="Loc2",
            celestial_object="Deep Sky",
            path="2.jpg",
            name="Image 2",
        )
        # Verify ordering (newest first)
        qs = AstroImage.objects.all()
        assert qs[0] == image2
        assert qs[1] == image1


@pytest.mark.django_db
class TestBackgroundMainPageModel:
    def test_string_representation(self):
        """Test BackgroundMainPage string representation"""
        bg = BackgroundMainPage.objects.create(image="bg.jpg")
        assert str(bg) == f"BackgroundMainPage {bg.pk}"
