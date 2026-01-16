from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    AstroImageViewSet,
    MainPageBackgroundImageView,
    MainPageLocationSliderViewSet,
)

app_name = "astroimages"

router = DefaultRouter()
router.register("image", AstroImageViewSet, basename="astroimage")
router.register("background", MainPageBackgroundImageView, basename="backgroundImage")
router.register("travel-highlights", MainPageLocationSliderViewSet, basename="travel-highlights")


urlpatterns = [
    path("", include(router.urls)),
]
