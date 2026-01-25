from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    AstroImageViewSet,
    CelestialObjectCategoriesView,
    MainPageBackgroundImageView,
    MainPageLocationViewSet,
    TagsView,
    TravelHighlightsBySlugView,
)

app_name = "astroimages"

router = DefaultRouter()
router.register("image", AstroImageViewSet, basename="astroimage")
router.register("background", MainPageBackgroundImageView, basename="backgroundImage")
router.register("travel-highlights", MainPageLocationViewSet, basename="travel-highlights")
router.register("tags", TagsView, basename="tags")


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
    path(
        "categories/",
        CelestialObjectCategoriesView.as_view(),
        name="celestial-object-categories",
    ),
    # ViewSet routes (general)
    path("", include(router.urls)),
]
