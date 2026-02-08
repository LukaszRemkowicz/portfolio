# translation/views.py
"""
Views for the translation app, providing dynamic styling and status endpoints.
"""

from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request

from django.conf import settings
from django.http import HttpResponse


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def admin_dynamic_parler_css_view(request: Request) -> HttpResponse:
    """
    Returns dynamically generated CSS to hide the 'X' (delete) button
    for the configured default/fallback language in Django Admin.
    """
    default_lang = getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", "en")

    css = f"""
    /* Dynamic Parler CSS generated for default language: {default_lang} */

    /*
       RULE 1: Inactive Tab
       Structure: <span class="available"><a href="?language={default_lang}">...</a> <a class="deletelink"></a></span>  # noqa: E501
       Target: .deletelink that is a sibling of the language link
    */
    .parler-language-tabs span a[href*="language={default_lang}"] ~ .deletelink,
    .parler-language-tabs span a[href*="language={default_lang}"] ~ .parler-delete {{
        display: none !important;
    }}

    /*
       RULE 2: Active Tab
       Structure: <input name="{default_lang}" ...> <span class="current">... <a class="deletelink"></a></span>  # noqa: E501
       Target: .deletelink inside the span that follows the input
    */
    .parler-language-tabs input[name="{default_lang}"] + span .deletelink,
    .parler-language-tabs input[name="{default_lang}"] + span .parler-delete {{
        display: none !important;
    }}
    """

    return HttpResponse(css, content_type="text/css")
