# Fail2ban Probe Blocker Playbook

Use this when enabling or operating production probe blocking on the VPS.

Current default policy for the repo-managed probe jails is 3 matching probes
from the same IP within 1 minute, followed by a permanent ban.

## Install / Enable

Run these commands on the production server:

```bash
sudo apt-get update
sudo apt-get install -y fail2ban

sudo mkdir -p /var/log/portfolio/traefik
sudo touch /var/log/portfolio/traefik/access.log

sudo infra/scripts/security/install_fail2ban_probe_blocker.sh

doppler run -- docker compose -f docker-compose.traefik.yml up -d traefik
sudo systemctl enable --now fail2ban
doppler run -- docker compose -f docker-compose.traefik.yml up -d --force-recreate traefik
```

The installer now detects the active nginx access-log path automatically and installs the shorter jail names required by `iptables`.
The host `fail2ban` log remains at `/var/log/fail2ban.log`.

The nginx container also mounts the downloaded user-agent blocklist at
`/etc/nginx/blocklist`. That blocklist rejects known bad user agents. The
fail2ban probe jails use access logs instead: they watch blocked sensitive path
requests, hidden-file requests, prohibited script/archive extensions, and common
CMS/PHP probe paths.

The Keycloak token jail watches failed `POST` requests to
`auth.lukaszremkowicz.com/realms/*/protocol/openid-connect/token`. It does not
ban normal OIDC discovery or JWKS reads.

Traefik and nginx are configured to trust `X-Forwarded-For` only from
Cloudflare edge ranges and private Traefik/nginx network ranges. This is
required so fail2ban bans the real visitor IP instead of a Cloudflare edge IP.
After changing those ranges, recreate Traefik and nginx before judging ban
behavior from access logs.

## After Repo Changes

When you change any of these repo-managed files:

- `infra/scripts/security/fail2ban/filter.d/portfolio-nginx-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/filter.d/portfolio-traefik-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/filter.d/portfolio-keycloak-token-abuse.conf`
- `infra/scripts/security/fail2ban/jail.d/portfolio-probe-blocker.local`
- `infra/scripts/security/install_fail2ban_probe_blocker.sh`

the running production `fail2ban` service does not pick them up automatically from the git checkout.

Apply the updated repo config on the server with:

```bash
sudo infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo fail2ban-client reload
```

Then verify the live jails:

```bash
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
sudo fail2ban-client status portfolio-keycloak-token
sudo tail -n 20 /var/log/fail2ban.log
```

Use `reload` after filter or jail changes. Use `restart` only if reload fails or the service needs recovery.

## Verify

Check service health and jail registration:

```bash
sudo systemctl status fail2ban --no-pager -l
sudo journalctl -u fail2ban -n 50 --no-pager
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
sudo fail2ban-client status portfolio-keycloak-token
```

Check whether the watched files are receiving traffic:

```bash
sudo ls -l /etc/nginx/logs/access.log
sudo tail -n 20 /etc/nginx/logs/access.log

sudo ls -l /var/log/portfolio/traefik/access.log
sudo tail -n 20 /var/log/portfolio/traefik/access.log
```

When traffic is proxied through Cloudflare, confirm the logged client IP is the
real visitor address, not a Cloudflare edge range such as `172.64.0.0/13`,
`172.68.0.0/16`, `162.158.0.0/15`, or `104.16.0.0/13`. If old bans include
Cloudflare edge IPs, unban them after deploying the real-IP fix.

If Traefik fails to start because the host-mounted access log is not writable, the container entrypoint now exits with a clear error instead of silently running without file logging. Check:

```bash
docker logs --tail 50 traefik
docker exec traefik sh -lc 'ls -ld /var/log/traefik && ls -l /var/log/traefik'
```

## Test Nginx Ban Flow

Generate a few blocked requests:

```bash
for i in 1 2 3; do curl -I https://lukaszremkowicz.com/.env; done
sudo fail2ban-client status portfolio-nginx-probes
sudo tail -n 20 /var/log/fail2ban.log
```

Expected result:

- `Currently banned: 1`
- the offending IP appears in `Banned IP list`
- `/var/log/fail2ban.log` shows `NOTICE [portfolio-nginx-probes] Ban <ip>`

The same policy applies to the Traefik probe jail for matching direct-IP or
host-header probes: 3 matching requests from one IP within 1 minute, then a
permanent ban.

## Test Keycloak Token Ban Flow

Generate a few failed token requests:

```bash
for i in 1 2 3; do
  curl -sS -o /dev/null -w "%{http_code}\n" -X POST \
    https://auth.lukaszremkowicz.com/realms/mcp/protocol/openid-connect/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=client_credentials" \
    --data-urlencode "client_id=codex-local" \
    --data-urlencode "client_secret=invalid"
done

sudo fail2ban-client status portfolio-keycloak-token
sudo tail -n 20 /var/log/fail2ban.log
```

Expected result:

- `Currently banned: 1`
- the offending IP appears in `Banned IP list`
- `/var/log/fail2ban.log` shows `NOTICE [portfolio-keycloak-token] Ban <ip>`

## Monitor

Useful day-to-day monitoring commands:

```bash
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes
sudo fail2ban-client status portfolio-keycloak-token

sudo tail -f /var/log/fail2ban.log
sudo journalctl -u fail2ban -f

sudo tail -f /etc/nginx/logs/access.log
sudo tail -f /var/log/portfolio/traefik/access.log
```

## Restart / Reload

Use these when updating config or recovering the service:

```bash
sudo systemctl restart fail2ban
sudo systemctl status fail2ban --no-pager -l

sudo fail2ban-client reload
sudo fail2ban-client status

doppler run -- docker compose -f docker-compose.traefik.yml up -d --force-recreate traefik
docker logs --tail 50 traefik
```

## Clean Banned IPs

Unban a single IP:

```bash
sudo fail2ban-client set portfolio-nginx-probes unbanip <ip>
sudo fail2ban-client set portfolio-traefik-probes unbanip <ip>
sudo fail2ban-client set portfolio-keycloak-token unbanip <ip>
```

Clear all bans by restarting the service:

```bash
sudo systemctl restart fail2ban
```

## Troubleshooting

If `fail2ban-client` reports a missing socket immediately after restart, wait a moment and retry. That can happen during service startup.

If `sudo infra/scripts/security/install_fail2ban_probe_blocker.sh` fails with a
permission error on an older server checkout, restore the executable bit once:

```bash
chmod +x infra/scripts/security/install_fail2ban_probe_blocker.sh
```

If the nginx jail sees failures but does not ban, check `/var/log/fail2ban.log` for `iptables` errors. Long jail names break chain creation, which is why the server must use:

- `portfolio-nginx-probes`
- `portfolio-traefik-probes`
- `portfolio-keycloak-token`

If the Traefik jail stays empty, confirm:

- the `traefik` container was recreated
- `/var/log/portfolio/traefik/access.log` is mounted and non-empty
- the jail appears in `sudo fail2ban-client status`
- `docker logs --tail 50 traefik` does not show `Traefik access log is not writable`
