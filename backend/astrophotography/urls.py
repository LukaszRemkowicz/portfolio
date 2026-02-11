from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    AstroImageViewSet,
    CelestialObjectCategoriesView,
    ImageURLViewSet,
    MainPageBackgroundImageView,
    MainPageLocationViewSet,
    SecureMediaView,
    TagsView,
    TravelHighlightsBySlugView,
)

app_name = "astroimages"

router = DefaultRouter()
router.register("astroimages", AstroImageViewSet, basename="astroimage")
router.register("background", MainPageBackgroundImageView, basename="backgroundImage")
router.register("travel-highlights", MainPageLocationViewSet, basename="travel-highlights")
router.register("tags", TagsView, basename="tags")
router.register("images", ImageURLViewSet, basename="image-urls")


urlpatterns = [
    # Secure Media Endpoint
    path(
        "images/<slug:slug>/serve/",
        SecureMediaView.as_view(),
        name="secure-image-serve",
    ),
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
    path(
        "categories/",
        CelestialObjectCategoriesView.as_view(),
        name="celestial-object-categories",
    ),
    # ViewSet routes (general)
    path("", include(router.urls)),
]
