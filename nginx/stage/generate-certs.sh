#!/bin/bash
# nginx/stage/generate-certs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/ssl"

mkdir -p "${SSL_DIR}"

if [[ -f "${SSL_DIR}/server.crt" ]]; then
    echo "⚠️  Self-signed certificate already exists. Skipping generation."
    exit 0
fi

echo "🔐 Generating self-signed SSL certificates for staging (*.portfolio.local)..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${SSL_DIR}/server.key" \
    -out "${SSL_DIR}/server.crt" \
    -subj "/C=PL/ST=Staging/L=Local/O=Portfolio/OU=Staging/CN=*.portfolio.local"

echo "✅ Certificates generated in ${SSL_DIR}"
