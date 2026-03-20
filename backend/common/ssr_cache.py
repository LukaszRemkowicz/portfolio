"""Helpers for notifying the frontend server about cache invalidation.

The backend uses these helpers after relevant content changes to ask the
frontend server to clear cached SSR shell data. Communication is done through
an internal HTTP webhook configured by environment variables.
"""

from __future__ import annotations

import json
import logging
from typing import Iterable, cast
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)


def invalidate_frontend_ssr_cache(tags: Iterable[str]) -> bool:
    """Send a cache invalidation webhook to the frontend server.

    Args:
        tags: Cache tags describing which frontend cache groups should be
            invalidated.

    Returns:
        ``True`` when the frontend invalidation endpoint responds with a 2xx
        status code. Returns ``False`` when the endpoint is not configured, no
        valid tags are provided, or the request fails.
    """

    invalidation_url = getattr(settings, "SSR_CACHE_INVALIDATION_URL", "")
    invalidation_token = getattr(settings, "SSR_CACHE_INVALIDATION_TOKEN", "")
    normalized_tags = sorted({tag for tag in tags if tag})

    if not invalidation_url or not normalized_tags:
        return False

    payload = json.dumps({"tags": normalized_tags}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    if invalidation_token:
        headers["Authorization"] = f"Bearer {invalidation_token}"

    try:
        req = request.Request(
            invalidation_url,
            data=payload,
            headers=headers,
            method="POST",
        )
        with request.urlopen(req, timeout=5) as response:
            status_code = cast(int, response.status)
            logger.info(
                "Frontend SSR cache invalidated: status=%s tags=%s",
                status_code,
                ",".join(normalized_tags),
            )
            return 200 <= status_code < 300
    except error.URLError as exc:
        logger.warning(
            "Frontend SSR cache invalidation failed for tags=%s: %s",
            ",".join(normalized_tags),
            exc,
        )
        return False
