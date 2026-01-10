from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import AstroImageViewSet, BackgroundMainPageView

app_name = "astroimages"

router = DefaultRouter()
router.register("image", AstroImageViewSet, basename="astroimage")
router.register("background", BackgroundMainPageView, basename="backgroundImage")


urlpatterns = [
    path("", include(router.urls)),
]
