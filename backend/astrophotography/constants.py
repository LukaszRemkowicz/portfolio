# backend/astrophotography/constants.py
from typing import List

from django.utils.translation import gettext_lazy as _

CELESTIAL_OBJECT_CHOICES = [
    ("Landscape", _("Landscape")),
    ("Deep Sky", _("Deep Sky")),
    ("Startrails", _("Startrails")),
    ("Solar System", _("Solar System")),
    ("Milky Way", _("Milky Way")),
    ("Northern Lights", _("Northern Lights")),
]


class MeteorDefaults:
    """
    Centralized default values for MeteorsMainPageConfig.
    Methods are used as callables for JSONField defaults to ensure
    each instance gets a fresh mutable object.
    """

    @staticmethod
    def star_path() -> List[int]:
        """
        [min, max] list representing the travel distance of a regular star in pixels.
        Example: [50, 500]
        """
        return [50, 500]

    @staticmethod
    def bolid_path() -> List[int]:
        """
        [min, max] list representing the travel distance of a bolid in pixels.
        Example: [50, 500]
        """
        return [50, 500]

    @staticmethod
    def star_streak() -> List[int]:
        """
        [min, max] list representing the visual length (streak) of a regular star in pixels.
        Example: [100, 200]
        """
        return [100, 200]

    @staticmethod
    def bolid_streak() -> List[int]:
        """
        [min, max] list representing the visual length (streak) of a bolid in pixels.
        Example: [20, 100]
        """
        return [20, 100]

    @staticmethod
    def star_opacity() -> List[float]:
        """
        [min, max] list (0.0 to 1.0) for regular star brightness.
        Example: [0.4, 0.8]
        """
        return [0.4, 0.8]

    @staticmethod
    def bolid_opacity() -> List[float]:
        """
        [min, max] list (0.0 to 1.0) for bolid brightness.
        Example: [0.7, 1.0]
        """
        return [0.7, 1.0]

    @staticmethod
    def smoke_opacity() -> List[float]:
        """
        [min, max] list (0.0 to 1.0) for the smoke trail of a bolid.
        Example: [0.5, 0.8]
        """
        return [0.5, 0.8]

    @staticmethod
    def star_duration() -> List[float]:
        """
        [min, max] list (seconds) representing the duration (speed) of a regular star.
        Example: [0.4, 1.2]
        """
        return [0.4, 1.2]

    @staticmethod
    def bolid_duration() -> List[float]:
        """
        [min, max] list (seconds) representing the duration (speed) of a bolid.
        Example: [0.4, 0.9]
        """
        return [0.4, 0.9]
