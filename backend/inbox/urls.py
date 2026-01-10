from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import views

app_name = "inbox"

router = DefaultRouter()
router.register(r"contact", views.ContactMessageViewSet, basename="contact-message")

urlpatterns = [
    path("", include(router.urls)),
]
