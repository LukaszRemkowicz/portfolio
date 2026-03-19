# Traefik Production Deployment Runbook

## Purpose

This is the canonical runbook for operating Traefik, production, and staging on the same server.

Use this document for:

- first-time server setup
- Traefik deployment
- production deployment
- staging deployment
- certificate storage and renewal behavior
- staging IP restriction updates
- post-deploy verification

This document reflects the current repository layout:

- Traefik config: [infra/traefik](/Users/lukaszremkowicz/Projects/landingpage/infra/traefik)
- nginx config: [infra/nginx](/Users/lukaszremkowicz/Projects/landingpage/infra/nginx)
- release scripts: [infra/scripts/release](/Users/lukaszremkowicz/Projects/landingpage/infra/scripts/release)
- DB backup scripts: [infra/scripts/db_backup](/Users/lukaszremkowicz/Projects/landingpage/infra/scripts/db_backup)

## Architecture

The server runs three major layers:

1. Traefik
2. Production application stack
3. Staging application stack

Production and staging are active at the same time on the same host.

Responsibilities:

- Traefik:
  - TLS termination
  - host routing
  - dashboard
  - staging IP allowlist
- nginx:
  - upstream proxying
  - static and media handling
  - protected media and `X-Accel-Redirect`
  - rate limits
- backend/frontend containers:
  - application runtime

## Project Naming

The compose project names are fixed:

- production: `portfolio-prod`
- staging: `portfolio-stage`

This keeps:

- container naming predictable
- volume naming stable
- log collection predictable
- release scripts consistent

## Certificates And ACME Storage

## Current Model

Traefik ACME state is stored in a Docker volume, not in the repository.

Current storage model:

- Docker volume: `portfolio_traefik_acme`
- container path: `/letsencrypt`
- ACME file path: `/letsencrypt/acme.json`

Related implementation files:

- [docker-compose.traefik.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.traefik.yml)
- [infra/traefik/traefik.yml](/Users/lukaszremkowicz/Projects/landingpage/infra/traefik/traefik.yml)
- [docker/traefik/entrypoint.sh](/Users/lukaszremkowicz/Projects/landingpage/docker/traefik/entrypoint.sh)

## Why This Matters

`acme.json` contains:

- ACME account registration data
- issued certificates
- private keys

It is runtime state. It should:

- survive container recreation
- stay out of git
- not be managed as a repo file

## Server Prerequisites

The SSH server needs:

- Docker
- Docker Compose v2
- git
- Doppler CLI
- external Docker network `traefik_proxy`
- host directories for logs and backups outside the repository:
  - `/var/log/portfolio/nginx/prod`
  - `/var/log/portfolio/nginx/stage`
  - `/var/backups/portfolio/prod`
  - `/var/backups/portfolio/pre_release/prod`

Create these directories explicitly on the server before deployment. Do not rely on Docker bind-mount side effects for `/var/log/...` paths.

Create the shared network once:

```bash
docker network create traefik_proxy
sudo mkdir -p /var/log/portfolio/nginx/prod
sudo mkdir -p /var/log/portfolio/nginx/stage
sudo mkdir -p /var/backups/portfolio/prod
sudo mkdir -p /var/backups/portfolio/pre_release/prod
```

## Required Docker Volumes

## Shared Traefik Volume

```bash
docker volume create portfolio_traefik_acme
```

## Production Volumes

```bash
docker volume create portfolio_prod_db_data
docker volume create portfolio_prod_media_data
docker volume create portfolio_prod_static_data
docker volume create portfolio_prod_celerybeat_data
docker volume create portfolio_prod_nginx_blocklist
docker volume create portfolio_prod_frontend_dist
```

## Staging Volumes

```bash
docker volume create portfolio_staging_db_data
docker volume create portfolio_staging_media_data
docker volume create portfolio_staging_static_data
docker volume create portfolio_staging_celerybeat_data
docker volume create portfolio_staging_nginx_blocklist
docker volume create portfolio_staging_frontend_dist
```

## Doppler Requirements

Traefik requires secrets such as:

- `CONTACT_EMAIL`
- `TRAEFIK_USER`
- `TRAEFIK_PASSWORD`
- `TRAEFIK_DASHBOARD_HOST`
- `STAGING_ALLOWED_IPS`

Application deploys require the normal backend/frontend environment secrets for each environment.

Do not keep local nginx certificate variables in production or staging Doppler configs:

- `NGINX_SSL_CERT`
- `NGINX_SSL_KEY`

Those variables are only used by local nginx. Production and staging terminate TLS at Traefik, not nginx.

Recommended split:

- Traefik: shared or production-grade infra config
- production app: prod config
- staging app: staging config

## First-Time Server Preparation

Run once on the SSH server:

```bash
cd ~/portfolio
git pull
docker network create traefik_proxy || true
sudo mkdir -p /var/log/portfolio/nginx/prod
sudo mkdir -p /var/log/portfolio/nginx/stage
sudo mkdir -p /var/backups/portfolio/prod
sudo mkdir -p /var/backups/portfolio/pre_release/prod
docker volume create portfolio_traefik_acme
docker volume create portfolio_prod_db_data
docker volume create portfolio_prod_media_data
docker volume create portfolio_prod_static_data
docker volume create portfolio_prod_celerybeat_data
docker volume create portfolio_prod_nginx_blocklist
docker volume create portfolio_prod_frontend_dist
docker volume create portfolio_staging_db_data
docker volume create portfolio_staging_media_data
docker volume create portfolio_staging_static_data
docker volume create portfolio_staging_celerybeat_data
docker volume create portfolio_staging_nginx_blocklist
docker volume create portfolio_staging_frontend_dist
```

## Release Safety

Production release now performs a pre-release database backup before migrations.

Operational meaning:

- container rollback is automatic only for app services
- schema rollback is still manual
- if a migration causes trouble, restore the pre-release dump rather than relying on app rollback alone

Default host paths:

- long-term backup container output: `/var/backups/portfolio/prod`
- pre-release safety backups: `/var/backups/portfolio/pre_release/prod`
- nginx logs: `/var/log/portfolio/nginx/prod` and `/var/log/portfolio/nginx/stage`

These paths should be created manually ahead of time:

```bash
sudo mkdir -p /var/backups/portfolio/prod
sudo mkdir -p /var/backups/portfolio/pre_release/prod
sudo mkdir -p /var/log/portfolio/nginx/prod
sudo mkdir -p /var/log/portfolio/nginx/stage
```

Production also refreshes the nginx bot blocklist during release. Staging relies primarily on the Traefik IP allowlist and does not require the blocklist refresh step for access control.

## Standard Deployment Order

Run deployments in this order:

1. Traefik
2. production
3. staging

Why:

- Traefik owns routing and TLS
- production should be validated first
- staging IP restriction is applied by Traefik

## Quick Start

## Deploy Traefik

```bash
ssh your-server
cd ~/portfolio
git pull
doppler run -c dev -- docker compose -f docker-compose.traefik.yml up -d --build
```

## Deploy Production

```bash
ssh your-server
cd ~/portfolio
git pull
doppler run -c dev -- env ENVIRONMENT=prod TAG=v1.2.3-YOURTAG ./infra/scripts/release/build.sh --emergency
doppler run -c dev -- env ENVIRONMENT=prod TAG=v1.2.3-YOURTAG ./infra/scripts/release/deploy.sh
```

## Deploy Staging

```bash
ssh your-server
cd ~/portfolio
git pull
doppler run -c stg -- env ENVIRONMENT=stage TAG=v1.2.3-YOURTAG ./infra/scripts/release/build.sh --emergency
doppler run -c stg -- env ENVIRONMENT=stage TAG=v1.2.3-YOURTAG ./infra/scripts/release/deploy.sh
```

## Full Procedure

## 1. Deploy Traefik

Run on the server:

```bash
cd ~/portfolio
git pull
doppler run -c dev -- docker compose -f docker-compose.traefik.yml up -d --build
```

What this does:

- builds the Traefik image
- renders the static config template with `CONTACT_EMAIL`
- generates dashboard htpasswd file from Doppler secrets
- mounts the ACME volume at `/letsencrypt`
- starts or updates the shared Traefik service

Validation:

```bash
docker compose -f docker-compose.traefik.yml ps
docker volume inspect portfolio_traefik_acme
docker logs traefik --tail 100
```

## 2. Deploy Production

Run on the server:

```bash
cd ~/portfolio
git pull
doppler run -c dev -- env ENVIRONMENT=prod TAG=v1.2.3-YOURTAG ./infra/scripts/release/build.sh --emergency
doppler run -c dev -- env ENVIRONMENT=prod TAG=v1.2.3-YOURTAG ./infra/scripts/release/deploy.sh
```

Validation:

```bash
docker compose -f docker-compose.prod.yml ps
docker logs portfolio-prod-be-1 --tail 100
docker logs portfolio-prod-nginx-1 --tail 100
```

## 3. Deploy Staging

Run on the server:

```bash
cd ~/portfolio
git pull
doppler run -c stg -- env ENVIRONMENT=stage TAG=v1.2.3-YOURTAG ./infra/scripts/release/build.sh --emergency
doppler run -c stg -- env ENVIRONMENT=stage TAG=v1.2.3-YOURTAG ./infra/scripts/release/deploy.sh
```

Validation:

```bash
docker compose -f docker-compose.stage.yml ps
docker logs portfolio-stage-be-1 --tail 100
docker logs portfolio-stage-nginx-1 --tail 100
```

## Staging IP Restriction

The staging allowlist is applied in Traefik, not in the staging compose file.

The active source of truth is:

- `STAGING_ALLOWED_IPS`
- interpolated into [docker-compose.traefik.yml](/Users/lukaszremkowicz/Projects/landingpage/docker-compose.traefik.yml)

Important operational rule:

- changing `STAGING_ALLOWED_IPS` requires a Traefik redeploy
- changing only the staging app does not update the allowlist

To apply a new allowlist:

```bash
ssh your-server
cd ~/portfolio
git pull
doppler run -c dev -- docker compose -f docker-compose.traefik.yml up -d --build
```

Recommended production usage:

- set explicit office/VPN/public `/32` or CIDR ranges
- do not leave `STAGING_ALLOWED_IPS` empty

## Database Names

Current database names:

- production: `portfolio_prod`
- staging: `portfolio_stage`
- local: `portfolio_dev`

The backup and restore scripts should resolve those names automatically.

## Database Restore

## Restore Production

```bash
ssh your-server
cd ~/portfolio
doppler run -c dev -- ./infra/scripts/db_backup/restore_db.sh ~/backups/prod_real.dump
```

## Restore Staging

```bash
ssh your-server
cd ~/portfolio
doppler run -c stg -- ./infra/scripts/db_backup/restore_db.sh ~/backups/stage.dump
```

## Media And Static Rules

Media handling remains owned by nginx and backend authorization rules:

- `/media/backgrounds/*` is public
- `/media/avatars/*` is public
- other `/media/*` is protected
- protected internal media paths are not directly public

This behavior should be validated after deployment.

## Post-Deploy Verification

## Production

```bash
curl -k -I https://your-prod-domain
curl -k -I https://your-admin-prod-domain/admin/
curl -k https://your-api-prod-domain/v1/travel-highlights/?lang=pl
```

Expected:

- homepage: `200`
- admin: normally `302` to login page
- API: `200`

## Staging

```bash
curl -k -I https://your-stage-domain
curl -k -I https://your-stage-admin-domain/admin/
curl -k https://your-stage-api-domain/v1/travel-highlights/?lang=pl
```

Expected:

- allowed IP: success
- non-allowed IP: `403`

## Dashboard

```bash
curl -k -I https://your-traefik-domain/dashboard/
```

Expected:

- auth challenge or authenticated success

Important:

- use `/dashboard/` with trailing slash

## Troubleshooting

## Certificates Not Issuing

Check:

- public DNS points to the server
- ports `80` and `443` are reachable
- `CONTACT_EMAIL` is set in Doppler
- Traefik logs do not show ACME validation errors

Useful command:

```bash
docker logs traefik --tail 200
```

## Staging Restriction Did Not Change

Cause:

- Traefik was not redeployed after changing `STAGING_ALLOWED_IPS`

Fix:

```bash
doppler run -c dev -- docker compose -f docker-compose.traefik.yml up -d --build
```

## Dashboard Returns 404

Usually the path is wrong.

Correct:

```text
https://your-traefik-domain/dashboard/
```

Not:

```text
https://your-traefik-domain/dashboard
```

## Old Project `acme.json` File Exists

It is obsolete.

Current certificate state lives in:

```text
portfolio_traefik_acme
```

## Operational Summary

For a normal server release:

1. `git pull`
2. deploy Traefik if routing, auth, TLS, or staging IP settings changed
3. deploy production
4. deploy staging
5. verify production routes
6. verify staging routes and IP restriction
7. verify dashboard

The key certificate rule is:

- never treat `acme.json` as a repo-managed file
- let Traefik manage `/letsencrypt/acme.json` inside `portfolio_traefik_acme`
