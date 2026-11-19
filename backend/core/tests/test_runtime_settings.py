import os
import subprocess
import sys


def read_settings(**environment):
    env = {**os.environ, **environment}
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from settings import base; print(base.SECRET_KEY, "
            "base.CACHES['default']['BACKEND'], base.CACHES['select2']['BACKEND'], "
            "base.BACKGROUND_TASK_WORKERS, base.SECURE_CONTENT_TYPE_NOSNIFF)",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_secret_is_required_outside_debug():
    result = read_settings(DEBUG="false", SECRET_KEY="")
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr


def test_debug_secret_default_and_cache_override():
    result = read_settings(
        DEBUG="true",
        SECRET_KEY="",
        CACHE_BACKEND="django.core.cache.backends.locmem.LocMemCache",
        BACKGROUND_TASK_WORKERS="3",
    )
    assert result.returncode == 0
    assert "django-insecure-development-key" in result.stdout
    assert result.stdout.count("django.core.cache.backends.locmem.LocMemCache") == 2
    assert result.stdout.rstrip().endswith("3 True")
