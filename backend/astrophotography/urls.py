from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'astroimages'

from .views import BackgroundMainPageView

router = DefaultRouter()
router.register('background', BackgroundMainPageView, basename='backgroundImage')


urlpatterns = [
    path('', include(router.urls)),
] 