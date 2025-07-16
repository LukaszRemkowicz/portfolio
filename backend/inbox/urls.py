from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our ViewSet
router = DefaultRouter()
router.register(r'contact-messages', views.ContactMessageViewSet, basename='contact-message')

app_name = 'inbox'

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Legacy endpoint for backward compatibility
    path('contact/', views.ContactMessageViewSet.as_view({'post': 'create'}), name='submit_contact_form'),
] 