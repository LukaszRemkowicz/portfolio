from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    AstroImageViewSet,
    MainPageBackgroundImageView,
    MainPageLocationSliderViewSet,
    TravelHighlightsBySlugView,
)

app_name = "astroimages"

router = DefaultRouter()
router.register("image", AstroImageViewSet, basename="astroimage")
router.register("background", MainPageBackgroundImageView, basename="backgroundImage")
router.register("travel-highlights", MainPageLocationSliderViewSet, basename="travel-highlights")


urlpatterns = [
    # Slug-based travel highlights endpoints (more specific routes first)
    path(
        "travel/<slug:country_slug>/<slug:place_slug>/",
        TravelHighlightsBySlugView.as_view(),
        name="travel-by-country-place",
    ),
    path(
        "travel/<slug:country_slug>/",
        TravelHighlightsBySlugView.as_view(),
        name="travel-by-country",
    ),
    # ViewSet routes (general)
    path("", include(router.urls)),
]
