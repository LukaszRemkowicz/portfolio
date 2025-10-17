from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

router = DefaultRouter()
router.register('profile', views.UserViewSet, basename='profile')

urlpatterns = [
    path('profile/', views.UserViewSet.as_view({'get': 'profile'}), name='profile'),
    path('', include(router.urls)),
] 