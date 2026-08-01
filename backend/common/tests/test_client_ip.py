from rest_framework.test import APIRequestFactory

from django.test import override_settings

from common.client_ip import get_client_ip
from common.throttling import TrustedAnonRateThrottle

request_factory = APIRequestFactory()


@override_settings(TRUSTED_PROXY_CIDRS=["172.16.0.0/12"])
def test_trusted_proxy_supplies_resolved_client_ip() -> None:
    request = request_factory.get(
        "/",
        REMOTE_ADDR="172.20.0.10",
        HTTP_X_REAL_IP="203.0.113.25",
        HTTP_X_FORWARDED_FOR="198.51.100.99",
        HTTP_CF_CONNECTING_IP="198.51.100.100",
    )

    assert get_client_ip(request) == "203.0.113.25"


@override_settings(TRUSTED_PROXY_CIDRS=["172.16.0.0/12"])
def test_untrusted_peer_cannot_spoof_client_ip() -> None:
    request = request_factory.get(
        "/",
        REMOTE_ADDR="198.51.100.10",
        HTTP_X_REAL_IP="203.0.113.25",
        HTTP_X_FORWARDED_FOR="203.0.113.26",
        HTTP_CF_CONNECTING_IP="203.0.113.27",
    )

    assert get_client_ip(request) == "198.51.100.10"


@override_settings(TRUSTED_PROXY_CIDRS=["172.16.0.0/12"])
def test_malformed_resolved_client_ip_falls_back_to_peer() -> None:
    request = request_factory.get(
        "/",
        REMOTE_ADDR="172.20.0.10",
        HTTP_X_REAL_IP="203.0.113.25, 198.51.100.10",
    )

    assert get_client_ip(request) == "172.20.0.10"


@override_settings(TRUSTED_PROXY_CIDRS=["172.16.0.0/12"])
def test_anonymous_throttle_uses_resolved_client_ip() -> None:
    first_request = request_factory.get(
        "/",
        REMOTE_ADDR="172.20.0.10",
        HTTP_X_REAL_IP="203.0.113.25",
    )
    second_request = request_factory.get(
        "/",
        REMOTE_ADDR="172.20.0.10",
        HTTP_X_REAL_IP="203.0.113.26",
    )
    throttle = TrustedAnonRateThrottle()

    assert throttle.get_ident(first_request) == "203.0.113.25"
    assert throttle.get_ident(second_request) == "203.0.113.26"
