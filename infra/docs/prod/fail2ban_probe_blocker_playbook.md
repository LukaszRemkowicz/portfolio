# Fail2ban Probe Blocker Playbook

Use this when enabling or operating production probe blocking on the VPS.

## Install / Enable

Run these commands on the production server:

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

The installer now detects the active nginx access-log path automatically and installs the shorter jail names required by `iptables`.

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

TAG=v2.2.0 doppler run -- docker compose -f docker-compose.traefik.yml up -d --force-recreate traefik
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

If the nginx jail sees failures but does not ban, check `/var/log/fail2ban.log` for `iptables` errors. Long jail names break chain creation, which is why the server must use:

- `portfolio-nginx-probes`
- `portfolio-traefik-probes`

If the Traefik jail stays empty, confirm:

- the `traefik` container was recreated
- `/var/log/portfolio/traefik/access.log` is mounted and non-empty
- the jail appears in `sudo fail2ban-client status`
- `docker logs --tail 50 traefik` does not show `Traefik access log is not writable`
