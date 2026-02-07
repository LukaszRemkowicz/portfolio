from datetime import date, timedelta
from typing import Optional

from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers
from rest_framework.serializers import ImageField

from django.conf import settings
from django.urls import reverse
from django.utils import translation

from common.utils.signing import generate_signed_url_params
from translation.services import TranslationService

from .models import (
    AstroImage,
    MainPageBackgroundImage,
    MainPageLocation,
    MeteorsMainPageConfig,
    Place,
    Tag,
)
from .services import GalleryQueryService


class TagSerializer(TranslatableModelSerializer):
    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    count = serializers.IntegerField(source="num_times", read_only=True)

    def get_name(self, instance: Tag) -> str:
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None
        return TranslationService.get_translation(instance, "name", lang)  # type: ignore[arg-type]

    def get_slug(self, instance: Tag) -> str:
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None
        return TranslationService.get_translation(instance, "slug", lang)  # type: ignore[arg-type]

    class Meta:
        model = Tag
        fields = ["name", "slug", "count"]


class BaseEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "model"]


class PlaceSerializer(TranslatableModelSerializer):
    country = serializers.CharField(source="country.name", read_only=True)

    def to_representation(self, instance: Place) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != settings.PARLER_DEFAULT_LANGUAGE_CODE:
            # Translate place name using Parler service
            data["name"] = TranslationService.get_translation(instance, "name", lang)

            # Translate country name using django-countries (native Django translation)
            with translation.override(lang):
                if instance.country:
                    data["country"] = instance.country.name

        return data  # type: ignore[no-any-return]

    class Meta:
        model = Place
        fields = ["id", "name", "country"]


class AstroImageBaseSerializer(TranslatableModelSerializer):
    """
    Base serializer for AstroImage, containing shared logic for URLs, tags, and translations.
    """

    url = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    process = serializers.BooleanField(source="zoom")
    place = PlaceSerializer(read_only=True)

    def get_url(self, obj: AstroImage) -> str:
        request = self.context.get("request")
        if request is None:
            return ""

        url_path = reverse("astroimages:secure-image-serve", kwargs={"slug": obj.slug})
        params = generate_signed_url_params(
            obj.slug, expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION
        )
        return f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"

    def get_tags(self, obj: AstroImage) -> list[str]:
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None
        return [TranslationService.get_translation(tag, "name", lang) for tag in obj.tags.all()]

    def to_representation(self, instance: AstroImage) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != settings.PARLER_DEFAULT_LANGUAGE_CODE:
            # Translate fields common to both (or specific ones if they exist in data)
            # We iterate over potential translatable fields.
            for field in ["name", "description", "exposure_details", "processing_details"]:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)

        return data  # type: ignore[no-any-return]

    class Meta:
        model = AstroImage
        fields = [
            "pk",
            "slug",
            "name",
            "url",
            "tags",
            "place",
            "capture_date",
            "process",
            "celestial_object",
        ]


class AstroImageSerializerList(AstroImageBaseSerializer):
    """
    Lightweight serializer for the gallery feed.
    Excludes heavy descriptions and technical details.
    """

    thumbnail_url = ImageField(source="thumbnail", read_only=True)

    class Meta(AstroImageBaseSerializer.Meta):
        fields = AstroImageBaseSerializer.Meta.fields + ["thumbnail_url", "description"]


class AstroImageSerializer(AstroImageBaseSerializer):
    """
    Detailed serializer for the modal/detail view.
    Includes full technical specs, equipment, and descriptions.
    """

    camera = serializers.StringRelatedField(many=True, read_only=True)
    lens = serializers.StringRelatedField(many=True, read_only=True)
    telescope = serializers.StringRelatedField(many=True, read_only=True)
    tracker = serializers.StringRelatedField(many=True, read_only=True)
    tripod = serializers.StringRelatedField(many=True, read_only=True)

    class Meta(AstroImageBaseSerializer.Meta):
        fields = AstroImageBaseSerializer.Meta.fields + [
            "description",
            "camera",
            "lens",
            "telescope",
            "tracker",
            "tripod",
            "exposure_details",
            "processing_details",
            "astrobin_url",
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
        fields = ["pk", "slug", "url", "thumbnail_url", "description"]


class MainPageLocationSerializer(TranslatableModelSerializer):
    place = PlaceSerializer(read_only=True)
    images = AstroImageThumbnailSerializer(many=True, read_only=True)
    background_image = serializers.SerializerMethodField()
    background_image_thumbnail = serializers.SerializerMethodField()
    adventure_date = serializers.SerializerMethodField()

    @staticmethod
    def format_date(dt: date) -> str:
        """Format: 20 Jan 2026"""
        return dt.strftime("%-d %b %Y")

    def get_background_image(self, obj: MainPageLocation) -> Optional[str]:
        if bg := obj.background_image:
            return str(bg.path.url)
        return None

    def get_background_image_thumbnail(self, obj: MainPageLocation) -> Optional[str]:
        if (bg := obj.background_image) and bg.thumbnail:
            return str(bg.thumbnail.url)
        return self.get_background_image(obj)

    def get_adventure_date(self, obj: MainPageLocation) -> Optional[str]:
        if not (dr := obj.adventure_date):
            return None

        lower = dr.lower
        upper = dr.upper

        if not lower:
            return None

        # upper represents the first day AFTER the range in PostgreSQL DateRange
        # So we subtract one day for display if it exists
        display_upper = upper - timedelta(days=1) if upper else None

        if not display_upper or lower == display_upper:
            return self.format_date(lower)

        # Smart formatting for ranges
        if lower.year == display_upper.year:
            if lower.month == display_upper.month:
                # 20 - 25 Jan 2026
                return f"{lower.day} - {display_upper.day} {lower.strftime('%b %Y')}"
            else:
                # 20 Jan - 05 Feb 2026
                return f"{lower.strftime('%-d %b')} - {display_upper.strftime('%-d %b %Y')}"

        # 20 Jan 2025 - 05 Jan 2026
        return f"{self.format_date(lower)} - {self.format_date(display_upper)}"

    def to_representation(self, instance: MainPageLocation) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != settings.PARLER_DEFAULT_LANGUAGE_CODE:
            # Translate fields
            for field in ["highlight_name", "story"]:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)

        return data  # type: ignore[no-any-return]

    class Meta:
        model = MainPageLocation
        fields = [
            "pk",
            "place",
            "place_slug",
            "country_slug",
            "highlight_name",
            "adventure_date",
            "story",
            "background_image",
            "background_image_thumbnail",
            "images",
            "created_at",
        ]


class TravelHighlightDetailSerializer(MainPageLocationSerializer):
    """
    Detailed serializer for the Travel Highlight page.
    Includes full image metadata and dynamic image filtering.
    """

    images = serializers.SerializerMethodField()  # type: ignore[assignment]

    def get_images(self, obj: MainPageLocation) -> list:
        queryset = GalleryQueryService.get_travel_highlight_images(obj)
        # Cast ReturnList to list to satisfy MyPy
        return list(AstroImageSerializerList(queryset, many=True, context=self.context).data)

    class Meta(MainPageLocationSerializer.Meta):
        fields = MainPageLocationSerializer.Meta.fields


class MeteorsMainPageConfigSerializer(serializers.ModelSerializer):
    randomShootingStars = serializers.BooleanField(source="random_stars_shooting")
    bolidChance = serializers.FloatField(source="bolid_chance")
    bolidMinInterval = serializers.IntegerField(source="bolid_interval")
    starPathRange = serializers.ListField(source="star_path_range")
    bolidPathRange = serializers.ListField(source="bolid_path_range")
    starStreakRange = serializers.ListField(source="star_streak_range")
    bolidStreakRange = serializers.ListField(source="bolid_streak_range")
    starDurationRange = serializers.ListField(source="star_duration_range")
    bolidDurationRange = serializers.ListField(source="bolid_duration_range")
    starOpacityRange = serializers.ListField(source="star_opacity_range")
    bolidOpacityRange = serializers.ListField(source="bolid_opacity_range")
    smokeOpacityRange = serializers.ListField(source="smoke_opacity_range")

    class Meta:
        model = MeteorsMainPageConfig
        fields = [
            "randomShootingStars",
            "bolidChance",
            "bolidMinInterval",
            "starPathRange",
            "bolidPathRange",
            "starStreakRange",
            "bolidStreakRange",
            "starDurationRange",
            "bolidDurationRange",
            "starOpacityRange",
            "bolidOpacityRange",
            "smokeOpacityRange",
        ]
