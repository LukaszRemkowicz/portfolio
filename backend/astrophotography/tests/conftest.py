from typing import Any

import pytest

from astrophotography.tests.factories import AstroImageFactory


@pytest.fixture
def astro_image(db: Any) -> Any:
    """Create a sample AstroImage for testing"""
    return AstroImageFactory()
