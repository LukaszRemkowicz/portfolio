# translation/views.py
"""
Views for the translation app, providing dynamic styling and status endpoints.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def admin_dynamic_parler_css_view(request: HttpRequest) -> HttpResponse:
    """
    Returns dynamically generated CSS to hide the 'X' (delete) button
    for the configured default/fallback language in Django Admin.
    """
    default_lang = settings.DEFAULT_APP_LANGUAGE

    css = f"""
    /* Dynamic Parler CSS generated for default language: {default_lang} */

    /*
       RULE 1: Inactive Tab
       Structure: <span class="available"><a href="?language={default_lang}">...</a>
       <a class="deletelink"></a></span>
       Target: .deletelink that is a sibling of the language link
    */
    .parler-language-tabs span a[href*="language={default_lang}"] ~ .deletelink,
    .parler-language-tabs span a[href*="language={default_lang}"] ~ .parler-delete {{
        display: none !important;
    }}

    /*
       RULE 2: Active Tab
       Structure: <input name="{default_lang}" ...> <span class="current">...
       <a class="deletelink"></a></span>
       Target: .deletelink inside the span that follows the input
    */
    .parler-language-tabs input[name="{default_lang}"] + span .deletelink,
    .parler-language-tabs input[name="{default_lang}"] + span .parler-delete {{
        display: none !important;
    }}
    """

    return HttpResponse(css, content_type="text/css")
