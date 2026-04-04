# Fail2ban Probe Blocker Playbook

Use this when enabling or operating production probe blocking on the VPS.

Current default ban window for the repo-managed probe jails is 7 days.

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
The host `fail2ban` log remains at `/var/log/fail2ban.log`, which is also the
path consumed by the collector when monitoring snapshots include firewall
activity.

## After Repo Changes

When you change any of these repo-managed files:

- `infra/scripts/security/fail2ban/filter.d/portfolio-nginx-sensitive-probes.conf`
- `infra/scripts/security/fail2ban/filter.d/portfolio-traefik-sensitive-probes.conf`
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
```

Check whether the watched files are receiving traffic:

```bash
sudo ls -l /etc/nginx/logs/access.log
sudo tail -n 20 /etc/nginx/logs/access.log

sudo ls -l /var/log/portfolio/traefik/access.log
sudo tail -n 20 /var/log/portfolio/traefik/access.log
```

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

## Monitor

Useful day-to-day monitoring commands:

```bash
sudo fail2ban-client status
sudo fail2ban-client status portfolio-nginx-probes
sudo fail2ban-client status portfolio-traefik-probes

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

If the Traefik jail stays empty, confirm:

- the `traefik` container was recreated
- `/var/log/portfolio/traefik/access.log` is mounted and non-empty
- the jail appears in `sudo fail2ban-client status`
- `docker logs --tail 50 traefik` does not show `Traefik access log is not writable`
