from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import AstroImageDetailView, AstroImageListView, BackgroundMainPageView

app_name = "astroimages"

router = DefaultRouter()
router.register("background", BackgroundMainPageView, basename="backgroundImage")


urlpatterns = [
    path("", include(router.urls)),
    path("image/", AstroImageListView.as_view(), name="astroimage-list"),
    path("image/<int:pk>/", AstroImageDetailView.as_view(), name="astroimage-detail"),
]
