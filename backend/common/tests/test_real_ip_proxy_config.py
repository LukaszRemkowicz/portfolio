import os
from pathlib import Path

REPOSITORY_ROOT = Path(os.environ.get("REPOSITORY_ROOT", Path(__file__).resolve().parents[3]))
NGINX_CONFIG = REPOSITORY_ROOT / "infra/nginx/static_server.conf"
FRONTEND_PROXY = REPOSITORY_ROOT / "frontend/server/backendProxy.js"


def test_nginx_logs_distinct_client_ip_evidence() -> None:
    config = NGINX_CONFIG.read_text()

    assert '"client_ip": "$remote_addr"' in config
    assert '"peer_ip": "$realip_remote_addr"' in config
    assert '"forwarded_for": "$http_x_forwarded_for"' in config
    assert '"cf_connecting_ip": "$http_cf_connecting_ip"' in config


def test_nginx_overwrites_upstream_client_identity() -> None:
    config = NGINX_CONFIG.read_text()

    assert "real_ip_header X-Forwarded-For;" in config
    assert "real_ip_recursive on;" in config
    assert "set_real_ip_from 10.0.0.0/8;" in config
    assert "set_real_ip_from 172.16.0.0/12;" in config
    assert "set_real_ip_from 192.168.0.0/16;" in config
    assert "proxy_set_header X-Real-IP $remote_addr;" in config
    assert "proxy_set_header X-Forwarded-For $remote_addr;" in config
    assert "$proxy_add_x_forwarded_for" not in config


def test_frontend_forwards_nginx_resolved_client_identity() -> None:
    proxy = FRONTEND_PROXY.read_text()

    assert "req.headers['x-real-ip']" in proxy
    assert "headers['X-Real-IP'] = resolvedClientIp" in proxy
    assert "headers['X-Forwarded-For'] = resolvedClientIp" in proxy
