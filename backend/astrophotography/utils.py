# backend/astrophotography/utils.py
from astrophotography.constants import CELESTIAL_OBJECT_CHOICES


def get_celestial_categories() -> list[str]:
    """Provide the list of celestial object categories."""
    return [choice[0] for choice in CELESTIAL_OBJECT_CHOICES]
