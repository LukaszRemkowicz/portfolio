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
    """Return the visitor IP resolved by a trusted internal proxy.

    Nginx supplies it as X-Real-IP. Requests from the Cloudflare Workers
    frontend arrive through the Cloudflare Tunnel (cloudflared) without
    X-Real-IP, which does not survive the Cloudflare edge; the Worker sets
    X-Forwarded-For to the visitor IP and Cloudflare appends its own hop, so
    the first entry is the visitor. Only trusted peers are believed.
    """

    peer_ip = _parse_ip(request.META.get("REMOTE_ADDR"))
    if peer_ip is None:
        return "unknown"

    if _is_trusted_proxy(peer_ip):
        real_ip_header = request.META.get("HTTP_X_REAL_IP")
        if real_ip_header is not None:
            resolved_client_ip = _parse_ip(real_ip_header)
            if resolved_client_ip is not None:
                return resolved_client_ip
            return peer_ip

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if isinstance(forwarded_for, str):
            first_hop = _parse_ip(forwarded_for.split(",")[0])
            if first_hop is not None:
                return first_hop

    return peer_ip
