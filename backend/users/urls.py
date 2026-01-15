from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import views

app_name = "users"

router = DefaultRouter()
router.register(r"", views.UserViewSet, basename="profile")

urlpatterns = [
    path("", include(router.urls)),
]
