from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import ShopProductViewSet

app_name = "shop"

router = DefaultRouter()
router.register("products", ShopProductViewSet, basename="shop-product")

urlpatterns = [
    path("", include(router.urls)),
]
