#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Target the nginx/ssl/certs directory relative to this script
SSL_DIR="$(cd "$SCRIPT_DIR/../../nginx/ssl/certs" 2>/dev/null || mkdir -p "$SCRIPT_DIR/../../nginx/ssl/certs" && cd "$SCRIPT_DIR/../../nginx/ssl/certs" && pwd)"

echo "Generating certificates in: $SSL_DIR"

# Generate self-signed certificate for portfolio.local, admin.portfolio.local, and api.portfolio.local
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/portfolio.local.key" \
    -out "$SSL_DIR/portfolio.local.crt" \
    -subj "/C=PL/ST=State/L=City/O=Organization/CN=portfolio.local" \
    -addext "subjectAltName=DNS:portfolio.local,DNS:admin.portfolio.local,DNS:api.portfolio.local"
