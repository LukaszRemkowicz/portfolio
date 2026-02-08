import pytest

from astrophotography.models import AstroImage
from astrophotography.tests.factories import AstroImageFactory


@pytest.fixture
def astro_image(db) -> AstroImage:
    """Create a sample AstroImage for testing"""
    return AstroImageFactory()
