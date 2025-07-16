from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'astroimages'

from .views import BackgroundMainPageView, AstroImageListView, AstroImageDetailView

router = DefaultRouter()
router.register('background', BackgroundMainPageView, basename='backgroundImage')


urlpatterns = [
    path('', include(router.urls)),
    path('image/', AstroImageListView.as_view(), name='astroimage-list'),
    path('image/<int:pk>/', AstroImageDetailView.as_view(), name='astroimage-detail'),
] 