"""Resolve the visitor IP supplied by a trusted internal reverse proxy."""

from ipaddress import ip_address, ip_network
from typing import Protocol

from django.conf import settings


class RequestWithMetadata(Protocol):
    META: dict[str, object]


def _parse_ip(value: object) -> str | None:
    if not isinstance(value, str) or not value or "," in value:
        return None
    try:
        return str(ip_address(value.strip()))
    except ValueError:
        return None


def _is_trusted_proxy(peer_ip: str) -> bool:
    address = ip_address(peer_ip)
    for cidr in settings.TRUSTED_PROXY_CIDRS:
        try:
            if address in ip_network(cidr):
                return True
        except ValueError:
            continue
    return False


def get_client_ip(request: RequestWithMetadata) -> str:
    """Return Nginx's resolved visitor IP only when the direct peer is trusted."""

    peer_ip = _parse_ip(request.META.get("REMOTE_ADDR"))
    if peer_ip is None:
        return "unknown"

    if _is_trusted_proxy(peer_ip):
        resolved_client_ip = _parse_ip(request.META.get("HTTP_X_REAL_IP"))
        if resolved_client_ip is not None:
            return resolved_client_ip

    return peer_ip
