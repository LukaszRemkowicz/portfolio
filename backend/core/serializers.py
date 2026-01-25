from rest_framework import serializers

from astrophotography.serializers import MeteorsMainPageConfigSerializer
from core.models import LandingPageSettings


class LandingPageSettingsSerializer(serializers.ModelSerializer):
    programming = serializers.BooleanField(source="programming_enabled", read_only=True)
    contactForm = serializers.BooleanField(source="contact_form_enabled", read_only=True)
    travelHighlights = serializers.BooleanField(source="travel_highlights_enabled", read_only=True)
    lastimages = serializers.BooleanField(source="lastimages_enabled", read_only=True)
    meteors = MeteorsMainPageConfigSerializer(read_only=True)

    class Meta:
        model = LandingPageSettings
        fields = [
            "programming",
            "contactForm",
            "travelHighlights",
            "lastimages",
            "meteors",
        ]
