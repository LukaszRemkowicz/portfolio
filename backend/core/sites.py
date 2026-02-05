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

    def get_app_list(  # noqa: C901
        self, request: HttpRequest, app_label: str = None
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

        new_app_list: List[Dict[str, Any]] = []

        # Create a lookup for existing apps and models for O(1) access
        # Structure: {'app_label': {'models': {'ModelName': model_dict, ...}, 'app_data': app_dict}}
        app_lookup: Dict[str, Any] = {}

        for app in app_list:
            label = app["app_label"]
            models_lookup = {model["object_name"]: model for model in app.get("models", [])}
            app_lookup[label] = {
                "app": app,
                "models": models_lookup,
            }

        # Build new list based on configuration
        for section in config:
            # handle 'app' or 'label' based sections

            # If "app" key is present, we try to source from an existing app
            if "app" in section:
                target_app_label = section["app"]

                # Check if this app exists in the original list
                # If not, skip (maybe permissions, or app doesn't exist)
                if target_app_label not in app_lookup:
                    continue

                original_app_data = app_lookup[target_app_label]

                # Copy the app dict structure
                new_app = original_app_data["app"].copy()

                # Override Label
                if "label" in section:
                    new_app["name"] = section["label"]
                    # Also update app_label to something unique if we are splitting
                    # one app into two?
                    # Django Admin Sidebar uses app_label as ID.
                    # If we have two sections from 'astrophotography', they might conflict in
                    # sidebar ID if not careful.
                    # But get_app_list returns a list, order matters.
                    # Let's hope Django frontend handles duplicate app_labels or we should fake it.
                    # Fake it by appending a suffix if needed?
                    # Actually, sidebar loops over app_list.

                # Filter/Reorder models
                if "models" in section:
                    ordered_models = []
                    target_models = section["models"]

                    for target_model in target_models:
                        # Parse 'app_label.ModelName' vs 'ModelName'
                        if "." in target_model:
                            t_app_label, t_model_name = target_model.split(".", 1)
                        else:
                            t_app_label, t_model_name = target_app_label, target_model

                        # Look up
                        if (
                            t_app_label in app_lookup
                            and t_model_name in app_lookup[t_app_label]["models"]
                        ):
                            model_data = app_lookup[t_app_label]["models"][t_model_name]
                            # We must use the original admin_url from the lookup
                            ordered_models.append(model_data)

                    # If we defined explicit models, overwrite the models list
                    if ordered_models:
                        new_app["models"] = ordered_models
                    else:
                        # If no models found (e.g. perms), skip this section completely
                        continue

                new_app_list.append(new_app)

            # Custom generic section (not backed by a single app)?
            # For now, only support app-backed sections as per ADMIN_REORDER config structure.

        return new_app_list
