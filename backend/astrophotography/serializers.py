from rest_framework import serializers

from .models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    MainPageLocation,
    Place,
    Telescope,
    Tracker,
    Tripod,
)


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "name"]


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ["id", "model"]


class LensSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lens
        fields = ["id", "model"]


class TelescopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telescope
        fields = ["id", "model"]


class TrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracker
        fields = ["id", "name"]


class TripodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tripod
        fields = [
            "name",
        ]


class AstroImageSerializerList(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)
    tags = serializers.StringRelatedField(many=True)
    camera = serializers.StringRelatedField(many=True)
    lens = serializers.StringRelatedField(many=True)
    telescope = serializers.StringRelatedField(many=True)
    tracker = serializers.StringRelatedField(many=True)
    tripod = serializers.StringRelatedField(many=True)
    location = serializers.CharField(source="location.name")

    class Meta:
        model = AstroImage
        fields = [
            "pk",
            "name",
            "description",
            "url",
            "thumbnail_url",
            "tags",
            "camera",
            "lens",
            "telescope",
            "tracker",
            "tripod",
            "capture_date",
            "location",
            "celestial_object",
            "created_at",
        ]


class AstroImageSerializer(serializers.ModelSerializer):
    camera = CameraSerializer(many=True, read_only=True)
    lens = LensSerializer(many=True, read_only=True)
    telescope = TelescopeSerializer(many=True, read_only=True)
    tracker = TrackerSerializer(many=True, read_only=True)
    tripod = TripodSerializer(many=True, read_only=True)

    location = serializers.CharField(source="location.name", read_only=True)

    class Meta:
        model = AstroImage
        fields = [
            "capture_date",
            "telescope",
            "camera",
            "tracker",
            "tripod",
            "lens",
            "location",
            "exposure_details",
            "processing_details",
            "celestial_object",
            "astrobin_url",
            "description",
        ]


class MainPageBackgroundImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")

    class Meta:
        model = MainPageBackgroundImage
        fields = ["url"]


class AstroImageThumbnailSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)

    class Meta:
        model = AstroImage
        fields = ["pk", "url", "thumbnail_url", "description"]


class MainPageLocationSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source="place.name", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)
    images = AstroImageThumbnailSerializer(many=True, read_only=True)
    background_image = serializers.SerializerMethodField()
    background_image_thumbnail = serializers.SerializerMethodField()
    adventure_date = serializers.SerializerMethodField()

    def get_background_image(self, obj):
        if obj.background_image:
            return obj.background_image.path.url
        return None

    def get_background_image_thumbnail(self, obj):
        if obj.background_image and obj.background_image.thumbnail:
            return obj.background_image.thumbnail.url
        return self.get_background_image(obj)

    def get_adventure_date(self, obj):
        if not obj.adventure_date:
            return None

        lower = obj.adventure_date.lower
        upper = obj.adventure_date.upper

        if not lower:
            return None

        # upper represents the first day AFTER the range in PostgreSQL DateRange
        # So we subtract one day for display if it exists
        from datetime import timedelta

        display_upper = upper - timedelta(days=1) if upper else None

        def format_date(dt):
            # Format: 20 Jan 2026
            return dt.strftime("%-d %b %Y")

        if not display_upper or lower == display_upper:
            return format_date(lower)

        # Smart formatting for ranges
        if lower.year == display_upper.year:
            if lower.month == display_upper.month:
                # 20 - 25 Jan 2026
                return f"{lower.day} - {display_upper.day} {lower.strftime('%b %Y')}"
            else:
                # 20 Jan - 05 Feb 2026
                return f"{lower.strftime('%-d %b')} - {display_upper.strftime('%-d %b %Y')}"

        # 20 Jan 2025 - 05 Jan 2026
        return f"{format_date(lower)} - {format_date(display_upper)}"

    class Meta:
        model = MainPageLocation
        fields = [
            "pk",
            "country",
            "country_name",
            "country_slug",
            "place_name",
            "place_slug",
            "highlight_name",
            "adventure_date",
            "story",
            "background_image",
            "background_image_thumbnail",
            "images",
            "created_at",
        ]
