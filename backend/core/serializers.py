from rest_framework import serializers

from django.db.models import Sum

from astrophotography.models import AstroImage
from astrophotography.serializers import MeteorsMainPageConfigSerializer
from core.models import LandingPageSettings


class LandingPageSettingsSerializer(serializers.ModelSerializer):
    TOTAL_TIME_SPENT_SAFETY_BUFFER_HOURS = 2

    programming = serializers.BooleanField(source="programming_enabled", read_only=True)
    contactForm = serializers.BooleanField(source="contact_form_enabled", read_only=True)
    travelHighlights = serializers.BooleanField(source="travel_highlights_enabled", read_only=True)
    lastimages = serializers.BooleanField(source="lastimages_enabled", read_only=True)
    total_time_spent = serializers.SerializerMethodField()
    meteors = MeteorsMainPageConfigSerializer(read_only=True)

    def get_total_time_spent(self, obj: LandingPageSettings) -> int:
        del obj
        aggregate = AstroImage.objects.aggregate(total=Sum("calculated_exposure_hours"))
        total_hours = float(aggregate["total"] or 0) + self.TOTAL_TIME_SPENT_SAFETY_BUFFER_HOURS
        fractional_hours = total_hours - int(total_hours)
        if fractional_hours < 0.5:
            return int(total_hours)
        return int(total_hours) + 1

    class Meta:
        model = LandingPageSettings
        fields = [
            "programming",
            "contactForm",
            "travelHighlights",
            "lastimages",
            "total_time_spent",
            "meteors",
        ]
