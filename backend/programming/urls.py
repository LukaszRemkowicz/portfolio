from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import ProjectViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
