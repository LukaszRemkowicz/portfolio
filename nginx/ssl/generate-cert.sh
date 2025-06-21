#!/bin/bash

# Create SSL directory if it doesn't exist
mkdir -p certs

# Generate self-signed certificate for portfolio.local and admin.portfolio.local
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/portfolio.local.key \
    -out certs/portfolio.local.crt \
    -subj "/C=PL/ST=State/L=City/O=Organization/CN=portfolio.local" \
    -addext "subjectAltName=DNS:portfolio.local,DNS:admin.portfolio.local" 