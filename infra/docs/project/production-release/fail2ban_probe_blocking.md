# Production Probe Blocking With Fail2ban

## Purpose

This runbook describes the production setup for automatic IP banning when
clients repeatedly probe sensitive paths such as:

- `/.env`
- `/app/.env`
- `/api/.env`
- `/.git/config`
- common CMS / exploit paths such as `/wp-admin` and `/xmlrpc.php`

The setup is intended for the single-droplet production deployment.

## Current Model

The blocking flow is:

1. Traefik logs unmatched direct-IP and host-header probes.
2. Nginx returns `403` / `404` for blocked sensitive paths on the public site.
3. `fail2ban` watches both log streams on the host.
4. Repeated probes from the same IP trigger a temporary host-level ban.

This complements the existing path blocking. It does not replace it.

## Repository Files

The repo-managed files are:

- `infra/scripts/security/fail2ban/filter.d/portfolio-nginx-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/filter.d/portfolio-traefik-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/jail.d/portfolio-probe-blocker.local`
- `infra/scripts/security/install_fail2ban_probe_blocker.sh`

Related runtime wiring:

- `infra/traefik/traefik.yml`
- `docker-compose.traefik.yml`

## Ban Policy

Current defaults:

- `findtime = 10m`
- `maxretry = 3`
- `bantime = 24h`

Jails:

- `portfolio-nginx-sensitive-probes`
- `portfolio-traefik-sensitive-probes`

## Host Prerequisites

Install `fail2ban` on the production VPS:

```bash
sudo apt-get update
sudo apt-get install -y fail2ban
```

Create the Traefik host log directory:

```bash
sudo mkdir -p /var/log/portfolio/traefik
sudo chown -R <user>:<user> /var/log/portfolio/traefik
```

## Deployment Steps

### 1. Deploy The Updated Traefik Config

Traefik now writes access logs to a host-mounted file:

```bash
TAG=vX.Y.Z doppler run -- docker compose -f docker-compose.traefik.yml up -d traefik
```

Verify the file exists and receives entries:

```bash
ls -l /var/log/portfolio/traefik/access.log
tail -f /var/log/portfolio/traefik/access.log
```

### 2. Install The Fail2ban Config

Run:

```bash
chmod +x /home/<user>/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo /home/<user>/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
```

This copies the filters and jail file into:

- `/etc/fail2ban/filter.d/`
- `/etc/fail2ban/jail.d/`

and reloads or restarts `fail2ban`.

## Server Playbook

What you still need to do on the server:

```bash
sudo apt-get update && sudo apt-get install -y fail2ban
sudo mkdir -p /var/log/portfolio/traefik
sudo chown -R <user>:<user> /var/log/portfolio/traefik
chmod +x /home/<user>/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo /home/<user>/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
TAG=v2.2.0 doppler run -- docker compose -f docker-compose.traefik.yml up -d traefik
```

Then verify:

```bash
sudo fail2ban-client status portfolio-nginx-sensitive-probes
sudo fail2ban-client status portfolio-traefik-sensitive-probes
```

## Verification

Check the configured jails:

```bash
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-sensitive-probes
sudo fail2ban-client status portfolio-traefik-sensitive-probes
```

Check active bans:

```bash
sudo fail2ban-client status portfolio-nginx-sensitive-probes
sudo fail2ban-client status portfolio-traefik-sensitive-probes
```

Look for the `Banned IP list` section.

## Log Sources

Nginx jail log file:

```text
/var/log/portfolio/nginx/prod/access.log
```

Traefik jail log file:

```text
/var/log/portfolio/traefik/access.log
```

## Tuning

You can adjust these values in:

- `infra/scripts/security/fail2ban/jail.d/portfolio-probe-blocker.local`

Common adjustments:

- lower `maxretry` to block faster
- reduce `findtime` to focus on short bursts
- increase `bantime` for longer lockouts

## Troubleshooting

### Traefik jail never bans

Check:

1. Traefik was recreated after the access-log file mount was added.
2. `/var/log/portfolio/traefik/access.log` exists and is non-empty.
3. `portfolio-traefik-sensitive-probes` appears in `fail2ban-client status`.

### Nginx jail never bans

Check:

1. Sensitive probe requests return `403` or `404`.
2. `/var/log/portfolio/nginx/prod/access.log` contains those requests.
3. `portfolio-nginx-sensitive-probes` appears in `fail2ban-client status`.

### A path is not triggering bans

Add or adjust the matching regex in:

- `infra/scripts/security/fail2ban/filter.d/portfolio-nginx-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/filter.d/portfolio-traefik-sensitive-probes.conf`

Then reinstall or reload `fail2ban`.
