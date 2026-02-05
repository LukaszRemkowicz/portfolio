# translation/urls.py
"""
URL configuration for the translation app.
"""
from django.urls import path

from .views import admin_dynamic_parler_css_view

app_name = "translation"

urlpatterns = [
    path(
        "admin/dynamic-parler-fixes.css",
        admin_dynamic_parler_css_view,
        name="admin-dynamic-css",
    ),
]
