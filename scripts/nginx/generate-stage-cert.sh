#!/bin/bash
# scripts/nginx/generate-stage-cert.sh

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Target the single centralized nginx/ssl/certs directory
SSL_DIR="$(cd "$SCRIPT_DIR/../../nginx/ssl/certs" 2>/dev/null || mkdir -p "$SCRIPT_DIR/../../nginx/ssl/certs" && cd "$SCRIPT_DIR/../../nginx/ssl/certs" && pwd)"

echo "Generating staging certificates in: $SSL_DIR"

# Generate self-signed certificate for staging local domains
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/stage.portfolio.local.key" \
    -out "$SSL_DIR/stage.portfolio.local.crt" \
    -subj "/C=PL/ST=State/L=City/O=Organization/CN=stage.portfolio.local" \
    -addext "subjectAltName=DNS:stage.portfolio.local,DNS:api.stage.portfolio.local,DNS:admin.stage.portfolio.local,DNS:staging.portfolio.local,DNS:api.staging.portfolio.local,DNS:admin.staging.portfolio.local"

echo "✅ Certificates generated in $SSL_DIR"
