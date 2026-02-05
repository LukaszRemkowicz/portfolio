# backend/core/__init__.py
"""
This will make sure the Celery app is always imported when Django starts
so that shared_task will use this app.
"""

try:
    from settings.celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:
    # where celery might not be installed (since tests run in Docker).
    pass
