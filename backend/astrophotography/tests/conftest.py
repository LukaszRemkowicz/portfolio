from typing import Any

import pytest


@pytest.fixture
def astro_image(db: Any) -> Any:
    """Create a sample AstroImage for testing"""
    from astrophotography.tests.factories import AstroImageFactory

    return AstroImageFactory()
