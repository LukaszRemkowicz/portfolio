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

- `portfolio-nginx-probes`
- `portfolio-traefik-probes`

## Host Prerequisites

Install `fail2ban` on the production VPS:

```bash
sudo apt-get update
sudo apt-get install -y fail2ban
```

Create the Traefik host log directory:

```bash
sudo mkdir -p /var/log/portfolio/traefik
sudo touch /var/log/portfolio/traefik/access.log
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
chmod +x /home/lukasz/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo /home/lukasz/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo systemctl enable --now fail2ban
```

This copies the filters and jail file into:

- `/etc/fail2ban/filter.d/`
- `/etc/fail2ban/jail.d/`

and reloads or restarts `fail2ban`.

## Server Playbook

What you still need to do on the server:

```bash
sudo apt-get update
sudo apt-get install -y fail2ban
sudo mkdir -p /var/log/portfolio/traefik
sudo touch /var/log/portfolio/traefik/access.log
chmod +x /home/lukasz/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo /home/lukasz/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
TAG=v2.2.0 doppler run -- docker compose -f docker-compose.traefik.yml up -d traefik
sudo systemctl enable --now fail2ban
TAG=v2.2.0 doppler run -- docker compose -f docker-compose.traefik.yml up -d --force-recreate traefik
```

Then verify:

```bash
sudo systemctl status fail2ban --no-pager -l
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
```

## Verification

Check the configured jails:

```bash
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
```

Check active bans:

```bash
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
```

Look for the `Banned IP list` section.

## Log Sources

Nginx jail log file:

```text
/var/log/portfolio/nginx/prod/access.log or /etc/nginx/logs/access.log
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
3. `portfolio-traefik-probes` appears in `fail2ban-client status`.

### Nginx jail never bans

Check:

1. Sensitive probe requests return `403` or `404`.
2. `/etc/nginx/logs/access.log` contains those requests.
3. `portfolio-nginx-probes` appears in `fail2ban-client status`.
4. `/var/log/fail2ban.log` does not show an `iptables` chain-name-too-long error.

### A path is not triggering bans

Add or adjust the matching regex in:

- `infra/scripts/security/fail2ban/filter.d/portfolio-nginx-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/filter.d/portfolio-traefik-sensitive-probes.conf`

Then reinstall or reload `fail2ban`.

## Operations

Monitor service and bans:

```bash
sudo systemctl status fail2ban --no-pager -l
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
sudo tail -f /var/log/fail2ban.log
sudo journalctl -u fail2ban -f
```

Check Traefik access-log health:

```bash
docker logs --tail 50 traefik
docker exec traefik sh -lc 'ls -ld /var/log/traefik && ls -l /var/log/traefik'
```

Restart or reload:

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client reload
```

Remove bans:

```bash
sudo fail2ban-client set portfolio-nginx-probes unbanip <ip>
sudo fail2ban-client set portfolio-traefik-probes unbanip <ip>
```

To clear all bans quickly, restart the service:

```bash
sudo systemctl restart fail2ban
```
