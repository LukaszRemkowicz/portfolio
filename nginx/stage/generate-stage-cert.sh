#!/bin/bash
# scripts/nginx/generate-stage-cert.sh

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Target the nginx/stage/ssl directory relative to this script
SSL_DIR="$(cd "$SCRIPT_DIR/../../nginx/stage/ssl" 2>/dev/null || mkdir -p "$SCRIPT_DIR/../../nginx/stage/ssl" && cd "$SCRIPT_DIR/../../nginx/stage/ssl" && pwd)"

echo "Generating certificates in: $SSL_DIR"

# Generate self-signed certificate for staging local domains
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -subj "/C=PL/ST=State/L=City/O=Organization/CN=stage.portfolio.local" \
    -addext "subjectAltName=DNS:stage.portfolio.local,DNS:api.stage.portfolio.local,DNS:admin.stage.portfolio.local,DNS:staging.portfolio.local,DNS:api.staging.portfolio.local,DNS:admin.staging.portfolio.local"
