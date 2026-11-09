"""Cloudflare R2 media storage: one Django storage routed over a public and a private bucket."""

# mypy: disable-error-code="no-any-return,import-untyped"

from typing import Any

from storages.backends.s3 import S3Storage

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

PRIVATE_ROOT = "images"
# Same contract as nginx: only generated thumbnail/detail variants are public. Sources
# (images/original/, legacy images/<file>) and high-resolution variants stay private.
PUBLIC_IMAGE_DIRS = frozenset({"thumbnail", "detail"})


def is_private_name(name: str) -> bool:
    """Private iff under ``images/`` and not inside a public variant directory."""
    parts = [p for p in str(name).replace("\\", "/").split("/") if p]
    if not parts or parts[0] != PRIVATE_ROOT:
        return False
    return not (len(parts) > 2 and parts[1] in PUBLIC_IMAGE_DIRS)


def is_remote_storage(storage: Any) -> bool:
    return bool(getattr(storage, "remote", False))


def _s3_kwargs(bucket: str, **extra: Any) -> dict[str, Any]:
    return {
        "bucket_name": bucket,
        "endpoint_url": settings.R2_ENDPOINT_URL,
        "access_key": settings.R2_ACCESS_KEY_ID,
        "secret_key": settings.R2_SECRET_ACCESS_KEY,
        "region_name": "auto",
        "signature_version": "s3v4",
        "file_overwrite": False,
        "default_acl": None,
        **extra,
    }


def public_kwargs(**extra: Any) -> dict[str, Any]:
    return _s3_kwargs(
        settings.R2_PUBLIC_BUCKET,
        custom_domain=settings.R2_PUBLIC_DOMAIN,
        url_protocol="https:",
        querystring_auth=False,
        **extra,
    )


def private_kwargs() -> dict[str, Any]:
    return _s3_kwargs(
        settings.R2_PRIVATE_BUCKET,
        querystring_auth=True,
        querystring_expire=settings.R2_SIGNED_URL_EXPIRE,
    )


@deconstructible
class R2RoutingStorage(Storage):
    """Routes each name to the public or private bucket; stored names stay unchanged."""

    remote = True

    def __init__(self) -> None:
        self._public = S3Storage(**public_kwargs())
        self._private = S3Storage(**private_kwargs())

    def _pick(self, name: str) -> S3Storage:
        return self._private if is_private_name(name) else self._public

    def _save(self, name: str, content: Any) -> str:
        return self._pick(name)._save(name, content)

    def get_available_name(self, name: str, max_length: int | None = None) -> str:
        return self._pick(name).get_available_name(name, max_length)

    def _open(self, name: str, mode: str = "rb") -> Any:
        return self._pick(name)._open(name, mode)

    def delete(self, name: str) -> None:
        self._pick(name).delete(name)

    def exists(self, name: str) -> bool:
        return self._pick(name).exists(name)

    def size(self, name: str) -> int:
        return self._pick(name).size(name)

    def url(self, name: str | None, *args: Any, **kwargs: Any) -> str:
        return self._pick(str(name)).url(name, *args, **kwargs)


class CKEditorR2Storage(S3Storage):
    """CKEditor 5 uploads: public bucket under ``ckeditor/``."""

    def __init__(self) -> None:
        super().__init__(**public_kwargs(location="ckeditor"))
