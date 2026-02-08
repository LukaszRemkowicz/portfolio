import logging
from typing import Any, Dict, List

from django.conf import settings
from django.contrib.admin import AdminSite
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class PortfolioAdminSite(AdminSite):
    """
    Custom AdminSite to reorder the admin index and sidebar based on settings.ADMIN_REORDER.
    Acts as a drop-in replacement for the default admin site.
    """

    site_header = "Portfolio Administration"
    site_title = "Portfolio Admin"
    index_title = "Home"

    def get_app_list(
        self, request: HttpRequest, app_label: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Return a comprehensive list of all installed apps that have been
        registered in this site.

        Overridden to implement manual reordering/grouping.
        """
        # Get the original list from default implementation
        app_list = super().get_app_list(request, app_label)

        # If config is missing, return original
        config = getattr(settings, "ADMIN_SITE_ORDERING", None)
        if not config:
            return app_list

        app_lookup = self._build_app_lookup(app_list)
        new_app_list: List[Dict[str, Any]] = []

        # Build new list based on configuration
        for section in config:
            if "app" in section:
                new_app = self._process_section(section, app_lookup)
                if new_app:
                    new_app_list.append(new_app)

        return new_app_list

    def _build_app_lookup(self, app_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Creates a lookup for existing apps and models for O(1) access."""
        app_lookup: Dict[str, Any] = {}
        for app in app_list:
            label = app["app_label"]
            models_lookup = {model["object_name"]: model for model in app.get("models", [])}
            app_lookup[label] = {
                "app": app,
                "models": models_lookup,
            }
        return app_lookup

    def _process_section(
        self, section: Dict[str, Any], app_lookup: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        """Processes an ADMIN_SITE_ORDERING section and returns a modified app dict."""
        target_app_label = section["app"]

        # Check if this app exists in the original list
        if target_app_label not in app_lookup:
            return None

        original_app_data = app_lookup[target_app_label]
        new_app: Dict[str, Any] = original_app_data["app"].copy()

        # Override Label
        if "label" in section:
            new_app["name"] = section["label"]

        # Filter/Reorder models
        if "models" in section:
            ordered_models = self._get_ordered_models(
                section["models"], target_app_label, app_lookup
            )
            if not ordered_models:
                return None
            new_app["models"] = ordered_models

        return new_app

    def _get_ordered_models(
        self, target_models: List[str], target_app_label: str, app_lookup: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Returns a list of model dicts based on section['models'] configuration."""
        ordered_models = []

        for target_model in target_models:
            # Parse 'app_label.ModelName' vs 'ModelName'
            if "." in target_model:
                t_app_label, t_model_name = target_model.split(".", 1)
            else:
                t_app_label, t_model_name = target_app_label, target_model

            # Look up
            if t_app_label in app_lookup and t_model_name in app_lookup[t_app_label]["models"]:
                model_data = app_lookup[t_app_label]["models"][t_model_name]
                ordered_models.append(model_data)

        return ordered_models
